def formatToListOfDict(dataToFormat, dictItems):
    # Declarare dictionar
    emptyDict = {}
    # Declarare lista de obiecte de tip dictionar
    dataToSend = []

    # Cream un model de dictionar pentru stocarea datelor
    for dictItem in dictItems:
        # Creare campuri dictionar si atribuire valori vide
        emptyDict[dictItem] = ''

    # Parcurgem datele de adaugat in lista de dictionare
    i = 0
    for data in dataToFormat:
        # Copiere dictionar
        eDict = dict(emptyDict)
        # Adaugam un dictionar gol pe care-l vom umple cu date
        dataToSend.append(eDict)
        # Adaugare date in dictionar
        index = 0;
        # Parcurgem campurile dictionarului si adaugam datele in
        # datele pe care urmeaza sa le returnam
        for dictItem in dictItems:
            dataToSend[i][dictItem] = dataToFormat[i][index]
            # Trecem la urmatoarul element de procesat
            index += 1
        # Trecem la urmatoarea linie de procesat
        i += 1

    # Returnare date formatate
    return dataToSend

