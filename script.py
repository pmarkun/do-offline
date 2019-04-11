from PyPDF2 import PdfFileMerger, PdfFileReader
import requests
import urllib.parse
import shutil
import os
import subprocess
import datetime
import unidecode
import fitz
import argparse

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
        self.do_filepath = "DO_{}_{}_{}_{}.pdf".format(self.caderno,self.ano,unidecode.unidecode(self.mes),self.dia)
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
        download = True
        while download:
            if not os.path.isfile(self.local_path + self.path + self.filename()):
                if self.getPagina():
                    self.pg += 1
                else:
                    if self.pg == 1:
                        return None
                    download = False
            else:
                self.pg += 1


    def mergeDO(self):
        x = [a for a in os.listdir(self.local_path + self.path) if a.endswith(".pdf")]
        x.sort()
        print(x)

        merger = PdfFileMerger()

        for pdf in x:
            pg = PdfFileReader(self.local_path + self.path + pdf)
            merger.append(pg)

        with open("data/tmp/"+self.do_filepath, "wb") as fout:
            print(fout)
            merger.write(fout)

    def highlightDO(self, words):
        doc = fitz.open("data/tmp/"+self.do_filepath)
        print(doc)
        for page in doc:
            for word in words:
                matches = page.searchFor(word)
                print(matches)
                for match in matches:
                    highlight = page.addHighlightAnnot(match)
        doc.save("data/tmp/h_"+self.do_filepath)


    def compactDO(self):
        self.compact_and_fix("data/tmp/h_"+self.do_filepath,"data/"+self.do_filepath)

    def compact_and_fix(self, infilepath, outfilepath):
        gscmd = ['gs', '-sDEVICE=pdfwrite',
         '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH',
         '-sOutputFile='+outfilepath, infilepath]
        gsproc = subprocess.call(gscmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def uploadDO(self):
        with open("data/"+self.do_filepath, 'rb') as arquivo:
            payload={
              "filename":self.do_filepath,
              "filetype":'pdf',
              "token": self.slack['token'],
              "channels": self.slack['channels'],
            }

            r = requests.post("https://slack.com/api/files.upload", params=payload, files={ 'file' : arquivo })

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", help="today or format DD/MM/YY")
    parser.add_argument("-c", "--caderno", help="legislativo, exec1, etc")
    args = parser.parse_args()

    if args.date == "today":
        d = datetime.datetime.now()
    else:
        d = datetime.datetime.strptime(args.date, "%d/%m/%y")

    ano = d.year
    mes = MESES[d.month - 1]
    dia = d.day
    caderno = args.caderno

    x = DO(ano,mes,dia,caderno, SETTINGS['slack'])
    if not os.path.isfile("data/"+x.do_filepath):
        print("Getting "+x.do_filepath)
        x.getDO()
        if x.pg > 1:
            x.mergeDO()
            x.highlightDO(SETTINGS['highlights'])
            x.compactDO()
            x.uploadDO()
    else:
        print(x.do_filepath+" already exists")
