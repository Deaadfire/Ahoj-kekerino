# Ahoj-kekerino
Projekt debugging
Projekt bere webové data z parl voleb 2017 a ukládá je do csv.
Zaměřuje se na vybraný územní celek (okres) https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ a dělá kumulativní výsledky pro všechny obce daného okresu.

Pro spuštění programu je potřeba vložit dva argumenty, URL okresu a název csv filu s .csv
Např. python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2101" "volby_benesov.csv"

Program nějak funguje, troufám si říct že dává i správná data.
Problém je u velkých okresů, hlavně u Prahy.
Asi nemám extra efektivní kód a připojuju se na danou webovku až moc často, že se začne bránit a odpojovat mě.
Tohle všechno mám pošéfené a teoreticky by to mělo po krátké pauze stejně všechno správně získat.

Např když má web odezvu 500, tak to chvilku počká a normálně pak pokračuje bez újmy na datech.

Problém nastává, když mě začíná web úplně blokovat a posílá tyto chyby:
Request failed: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')), attempt 1/6
Request failed: HTTPSConnectionPool(host='www.volby.cz', port=443): Max retries exceeded with url: /pls/ps2017nss/ps311?xjazyk=CZ&xkraj=1&xobec=547387&xokrsek=15017&xvyber=1100 (Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1035)'))), attempt 2/6

Měl jsem za to, že to mám nějak pošéfené a taky to pak projde v pohodě, ale začal jsem si všímat, že i když se to tváří OK a nevyhazuje to nějaké jiné chyby ve funkcích, tak reálně výsledná data jsou jiná.
Stává se to fakt jen u těch velkých (testuju to na Praze) - přidal jsem i csv file s Prahou, kde si myslím že výsledky jsou ok
Kontroluju to vždy na počtu Registered celkových, což by mělo myslím být 916940.

Tohle číslo dostanu když mi skáčou max chyby 500.
Když ale skáčou ty další chyby, dostávám číslo menší např. 914k, 915k atp. - Jde to většinou z jedné/dvou oblastí, např Praha 14 
Vystopoval jsem, že tam chybí vždycky třeba data za jeden podokrsek, např zde: https://www.volby.cz/pls/ps2017nss/ps33?xjazyk=CZ&xkraj=1&xobec=547361 jednou chyběly data za celý 14002 - a tak se to děje snad vždy, ne že by chyběly části více okrsků, ale třeba vždy jen jeden dva úplně.

A nedokážu to nějak podchytit ani zachytit, ani přijít na to kde to dělám špatně.
A debuggovat fakt moc neumím no :D

Př. spuštění pro prahu teda je:
python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=1&xnumnuts=1100" "volby_praha.csv"

Mohl bys to prosím zkusit párkrát spustit dokud nenasimuluješ nekompletní csv a zkusit přijít na proč a co s tím můžu udělat?
Mě to většinou funguje třeba 4x v řadě okay jen chyby 500 a výsledek komplet, ale pak už se to webu přestane líbit a na 5. pokus to začne házet ty jiné errory a výsledky bad.

V životě jsem webscrapping nedělal a vím jen to, co mě naučilo AI prakticky :D
