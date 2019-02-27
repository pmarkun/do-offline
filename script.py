from urllib.request import urlopen
from PyPDF2 import PdfFileMerger
import shutil
import os
import subprocess


BASE_URL = "http://diariooficial.imprensaoficial.com.br/doflash/prototipo/"
DIRECTORY = "{}/{}/{}/{}/pdf/"
PG = "pg_{}.pdf"

ano = 2019
mes = 'Fevereiro'
dia = 27
caderno = 'legislativo'


def getPagina(ano,mes,dia,caderno,pg):
    d = DIRECTORY.format(ano,mes,dia,caderno)
    p = PG.format(str(pg).zfill(4))

    if not os.path.exists(d):
        os.makedirs(d)

    url = BASE_URL + d + p
    resp = urlopen(url)
    if resp.code == 200:
        with open(d+p, 'wb') as out_file:
            shutil.copyfileobj(resp, out_file)
        return 1
    else:
        return None

def getDO(ano,mes,dia,caderno):
    pg = 1
    download = 1
    while download == 1:
        d = DIRECTORY.format(ano,mes,dia,caderno)
        p = PG.format(str(pg).zfill(4))
        if not os.path.isfile(d+p):
            do = getPagina(ano,mes,dia,caderno,pg)
            if do:
                pg += 1
            else:
                download = 0
        else:
            print("arquivo ja baixado")
            pg += 1

def mergeDO(ano,mes,dia,caderno):
    d = os.path.dirname(os.path.abspath(__file__)) + "/" + DIRECTORY.format(ano,mes,dia,caderno)
    print(d)
    x = [a for a in os.listdir(d) if a.endswith(".pdf")]
    x.sort()
    print(x)

    merger = PdfFileMerger()

    for pdf in x:
        merger.append(open(d+pdf, 'rb'))

    with open("DO_{}_{}_{}_{}.pdf".format(caderno,ano,mes,dia), "wb") as fout:
        merger.write(fout)


#RODAR gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen -dNOPAUSE -dBATCH  -dQUIET -sOutputFile=output.pdf input.pdf
#COMPRIMIR E ENVIAR PDF POR EMAIL
