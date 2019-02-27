from urllib.request import urlopen
import shutil
import os

BASE_URL = "http://diariooficial.imprensaoficial.com.br/doflash/prototipo/"
DIRECTORY = "{}/{}/{}/{}/pdf/"
PG = "pg_{}.pdf"

ano = 2019
mes = 'Fevereiro'
dia = 27
caderno = 'legislativo'
pg = 1


def getDO(ano,mes,dia,caderno,pg):
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

download = 1
while download == 1:
    d = DIRECTORY.format(ano,mes,dia,caderno)
    p = PG.format(str(pg).zfill(4))
    if not os.path.isfile(d+p):
        do = getDO(ano,mes,dia,caderno,pg)
        if do:
            pg += 1
        else:
            download = 0
    else:
        print("arquivo ja baixado")
        pg += 1
