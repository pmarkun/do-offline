from PyPDF2 import PdfFileMerger
import requests
import shutil
import os
import subprocess
import datetime

MESES = ['Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
class DO:
    def __init__(self, ano, mes, dia, caderno):
        self.ano = ano
        self.mes = mes
        self.dia = dia
        self.caderno = caderno
        self.pg = 1
        self.base_url = "http://diariooficial.imprensaoficial.com.br/doflash/prototipo/"
        self.path = "{}/{}/{}/{}/pdf/".format(ano,mes,dia,caderno)
        self.do_filepath = "DO_{}_{}_{}_{}.pdf".format(self.caderno,self.ano,self.mes,self.dia)

    def filename(self):
        return "pg_{}.pdf".format(str(self.pg).zfill(4))

    def getPagina(self):
        print("Baixando pg "+str(self.pg))
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        url = self.base_url + self.path + self.filename()
        print(url)
        resp = requests.get(url)

        if resp.status_code == 200:
            with open(self.path + self.filename(), 'wb') as out_file:
                for chunk in resp.iter_content(1024):
                    out_file.write(chunk)
            return True
        elif resp.status_code == 404:
            return False

    def getDO(self):
        download = 1
        while download == 1:
            if not os.path.isfile(self.path + self.filename()):
                if self.getPagina():
                    self.pg += 1
                else:
                    download = 0
            else:
                self.pg += 1

    def mergeDO(self):
        x = [a for a in os.listdir(self.path) if a.endswith(".pdf")]
        x.sort()
        print(x)

        merger = PdfFileMerger()

        for pdf in x:
            merger.append(open(self.path+pdf, 'rb'))

        with open(self.do_filepath, "wb") as fout:
            merger.write(fout)

    def compactDO(self):
        outfile = '-sOutputFile=s_'+self.do_filepath
        gscmd = ['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH', outfile, self.do_filepath]
        gsproc = subprocess.call(gscmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

#REFATORAR CODIGO P/ USAR CLASSES
#RODAR gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen -dNOPAUSE -dBATCH  -dQUIET -sOutputFile=output.pdf input.pdf
#COMPRIMIR E ENVIAR PDF POR EMAIL

if __name__ == "__main__":

    d = datetime.datetime.now()
    ano = d.year
    mes = MESES[d.month-1]
    dia = d.day-9
    caderno = 'legislativo'

    x = DO(ano,mes,dia,caderno)
    if not os.path.isfile(x.do_filepath):
        print("Getting "+x.do_filepath)
        x.getDO()
        x.mergeDO()
        x.compactDO()
    else:
        print(x.do_filepath+" already exists")
