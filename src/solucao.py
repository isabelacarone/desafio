import pandas as pd
import numpy as np

def extrair_nr_dias(nome_dia: str) -> int:
    ''' retira o Dia_ e deixa só o numero referente ao dia 
        ex: Dia_15 -> 15
    '''
    try: 
        partes = str(nome_dia).split('_')
        numero = int(partes[-1])
        return numero
    except:
        return 0 



