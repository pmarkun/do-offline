from PyPDF2 import PdfFileMerger
import requests
import urllib.parse
import shutil
import os
import subprocess
import datetime
import unidecode

from settings import *

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
class DO:
    def __init__(self, ano, mes, dia, caderno, slackconfig):
        self.ano = ano
        self.mes = mes
        self.dia = str(dia).zfill(2)
        self.caderno = caderno
        self.pg = 1
        self.base_url = "http://diariooficial.imprensaoficial.com.br/doflash/prototipo/"
        self.local_path = "data/raw/"
        self.path = "{}/{}/{}/{}/pdf/".format(self.ano,self.mes,self.dia,self.caderno)
        self.do_filepath = "data/DO_{}_{}_{}_{}.pdf".format(self.caderno,self.ano,unidecode.unidecode(self.mes),self.dia)
        self.slack = slackconfig

    def filename(self):
        return "pg_{}.pdf".format(str(self.pg).zfill(4))

    def getPagina(self):
        print("Baixando pg "+str(self.pg))
        if not os.path.exists(self.local_path + self.path):
            os.makedirs(self.local_path + self.path)

        url = self.base_url + urllib.parse.quote(self.path) + self.filename()
        print(url)
        resp = requests.get(url)

        if resp.status_code == 200:
            with open(self.local_path + self.path + self.filename(), 'wb') as out_file:
                for chunk in resp.iter_content(1024):
                    out_file.write(chunk)
            return True
        elif resp.status_code == 404:
            return False

    def getDO(self):
        download = 1
        while download == 1:
            if not os.path.isfile(self.local_path + self.path + self.filename()):
                if self.getPagina():
                    self.pg += 1
                else:
                    download = 0
            else:
                self.pg += 1
        self.mergeDO()

    def mergeDO(self):
        x = [a for a in os.listdir(self.local_path + self.path) if a.endswith(".pdf")]
        x.sort()
        print(x)

        merger = PdfFileMerger()

        for pdf in x:
            merger.append(open(self.local_path + self.path+pdf, 'rb'))

        with open(self.do_filepath, "wb") as fout:
            merger.write(fout)
        self.compactDO()

    def compactDO(self):
        outfile = '-sOutputFile=s_'+self.do_filepath
        gscmd = ['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH', outfile, self.do_filepath]
        gsproc = subprocess.call(gscmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.do_filepath = 's_'+self.do_filepath

    def uploadDO(self):
        with open(self.do_filepath, 'rb') as arquivo:
            payload={
              "filename":self.do_filepath,
              "filetype":'pdf',
              "token": self.slack['token'],
              "channels": self.slack['channels'],
            }

            r = requests.post("https://slack.com/api/files.upload", params=payload, files={ 'file' : arquivo })

if __name__ == "__main__":

    d = datetime.datetime.now()
    ano = d.year
    mes = MESES[d.month-1]
    dia = d.day
    caderno = 'legislativo'

    x = DO(ano,mes,dia,caderno, SETTINGS['slack'])

    if not os.path.isfile(x.do_filepath):
        print("Getting "+x.do_filepath)
        x.getDO()
        x.uploadDO()
    else:
        print(x.do_filepath+" already exists")
