from flask import Flask, render_template, request
import pyodbc
import formatData
import datetime

# definirea aplicatiei
app = Flask(__name__, template_folder='templates')


# pagina de login
@app.route('/', methods=['POST', 'GET'])
def main():
    correctPassword=  'parola'
    if request.method == "POST":
        parola = request.form.get('parola')
        if parola == correctPassword:
            # verificam daca parola introdusa este cea corecta
            return render_template('main.html')
        else:
            return render_template('login.html', parolaGresita=1)
    return render_template('login.html', parolaGresita=0)


# meniul principal
@app.route('/meniu')
def meniu():
    return render_template('main.html')


# ruta default, nefolosita
@app.route('/index')
def index():
    return render_template('index.html')


# pagina "Doctori"
@app.route('/doctori', methods=['POST', 'GET'])
def data():
    cursor = conn.cursor()
    # facem legatura cu baza de date

    stergere = 0

    if request.method == "POST":
        # unul dintre formulare a trimis date
        pressed = request.form.get('toggleStergere')
        if pressed is not None:
            # se modifica optiunea de stergere
            stergere = request.form.get('delete')
            if stergere == 'DA':
                stergere = 1
            else:
                stergere = 0

        idDoctorSters = request.form.get('idDoctor')
        if idDoctorSters is not None:
            # am primit un id de doctor petru sters
            cursor.execute("DELETE FROM doctori WHERE doctorid = " + str(idDoctorSters))
            conn.commit()

        doctorID = request.form.get('schimbaDisponibilitatea')

        if doctorID is not None:
            # am primit un id pentru a schimba disponibilitatea unui doctor
            cursor.execute("select Disponibil from doctori where doctorid = " + str(doctorID))
            disponibil = cursor.fetchall()
            disponibil = not disponibil[0][0]
            if disponibil == True:
                disp = 1
            else:
                disp = 0
            cursor.execute(
                "update Doctori set Disponibil = " + str(disp) + " where doctorid = " + str(doctorID))

        receivedAge = request.form.get('searchData')

        if receivedAge is not None:
            # trebuie efectuata cautarea dupa varsta
            birthYear = 2021 - int(receivedAge)
            cursor.execute("SELECT DoctorID, Nume, Prenume, DataNasterii, disponibil FROM Doctori WHERE doctorid in (select dd.doctorid from doctori dd where year(dd.datanasterii) = " + str(birthYear) + ")")
        else:
            # trebuie efectuata cautarea dupa nume/prenume
            formsData = request.form.get("searchText")
            if formsData is None:
                formsData = ''
            cursor.execute(
                "SELECT DoctorID, Nume, Prenume, DataNasterii, disponibil FROM Doctori where nume like '%" + str(
                    formsData) + "%' or prenume like '%" + str(formsData) + "%'")

    else:
        # se extrag toti doctorii din baza de date, fara restrictii
        cursor.execute("SELECT DoctorID, Nume, Prenume, DataNasterii, disponibil FROM Doctori")
    data = cursor.fetchall()
    cursor.close()
    dataToDisplay = formatData.formatToListOfDict(data, ['ID', 'Nume', 'Prenume', 'DN', 'disponibil'])
    # formatam rezultatul query-ului sub forma de vector de dictionare

    return render_template('data.html', data=dataToDisplay, canDelete=stergere)


# pagina "Pacienti"
@app.route('/pacienti', methods=['POST', 'GET'])
def pacienti():
    cursor = conn.cursor()
    # facem legatura cu baza de date

    stergere = 0

    if request.method == 'POST':
        # am primit date de la un formular
        pressed = request.form.get('toggleStergere')
        if pressed is not None:
            # se modifica optiunea de stergere
            stergere = request.form.get('delete')
            if stergere == 'DA':
                stergere = 1
            else:
                stergere = 0

        idPacientSters = request.form.get('idPacient')
        if idPacientSters is not None:
            # am primit id-ul unui pacient pentru sters
            cursor.execute("DELETE FROM Pacienti WHERE pacientId = " + str(idPacientSters))
            conn.commit()

        nrDoctori = request.form.get("searchData")

        if nrDoctori is not None:
            # se executa cautarea dupa numarul de doctori
            cursor.execute("select p.pacientid, p.nume, p.prenume, count(distinct c.doctorid) from Pacienti p left "
                           "join Consultatii c on p.PacientID = c.PacientID where p.pacientid in (select pp.pacientid "
                           "from pacienti pp left join Consultatii cc on pp.PacientID = cc.PacientID group by "
                           "pp.pacientid having count(distinct cc.doctorid) = " + str(nrDoctori) + ") group by p.pacientid, p.nume, "
                           "p.prenume order by p.pacientid")
        else:
            # se executa cautarea dupa text
            formsData = request.form.get("searchText")
            if formsData is None:
                formsData = ''
            cursor.execute(
                "select p.pacientid, p.nume, p.prenume, count(distinct c.doctorid) from Pacienti p left join "
                "Consultatii c on p.PacientID = c.PacientID where p.nume like '%" + str(formsData) + "%' "
                                                                                                     "or p.prenume like '%" + str(
                    formsData) + "%' group by p.pacientid, p.nume, p.prenume "
                                 "order by p.pacientid")

    else:
        # se extrag toate informatiile despre pacienti, fara restrictii
        cursor.execute(
            "select p.pacientid, p.nume, p.prenume, count(distinct c.doctorid) from Pacienti p left join Consultatii c on "
            "p.PacientID = c.PacientID group by p.pacientid, p.nume, p.prenume order by p.pacientid")

    data = cursor.fetchall()
    doctorDataToDisplay = []
    dataToDisplay = formatData.formatToListOfDict(data, ['id', 'nume', 'prenume', 'nrDoctori'])
    # formatam rezultatul query-ului sub forma de vector de dictionare

    # cautam toti doctorii care au consultat pacientii
    cursor.execute(
            "select p.pacientid, p.nume, p.prenume, count(distinct c.doctorid) from Pacienti p left join Consultatii c on "
            "p.PacientID = c.PacientID group by p.pacientid, p.nume, p.prenume order by p.pacientid")

    personsData = cursor.fetchall()
    persons = formatData.formatToListOfDict(personsData, ['id', 'nume', 'prenume', 'nrDoctori'])
    # formatam rezultatul query-ului sub forma de vector de dictionare


    # dupa ce am pregatit datele, le transformam intr-un vector de obiecte continand informatii despre doctori
    # fiecare rand (obiect din vector) contine la randul sau obiectele de tip doctor pentru persoana cu id-ul pozitiei respective
    for person in persons:
        cursor.execute("select distinct d.nume, d.prenume, p.pacientId from doctori d inner join consultatii c on c.doctorid = d.doctorid "
                       "inner join pacienti p on p.pacientid = c.pacientid where p.pacientid = " + str(person['id'])
                       + " order by p.pacientid")
        doctorData = cursor.fetchall()
        doctorDataRow = formatData.formatToListOfDict(doctorData, ['nume', 'prenume', 'pacientId'])
        doctorDataToDisplay.append(doctorDataRow)
    #   datele care vor fi trimise spre afisare in html vor fi continute in acest vector


    cursor.close()
    return render_template('pacienti.html', data=dataToDisplay, doctorData=doctorDataToDisplay, canDelete=stergere)


# pagina "Consultatii"
@app.route('/consultatii', methods=['POST', 'GET'])
def consultatii():
    cursor = conn.cursor()
    # realizam legatura cu baza de date

    stergere = 0

    if request.method == 'POST':
        # am primit informatii de la un formular

        pressed = request.form.get('toggleStergere')
        if pressed is not None:
            # se modifica optiunea pentru meniul de stergere
            stergere = request.form.get('delete')
            if stergere == 'DA':
                stergere = 1
            else:
                stergere = 0

        idConsultatieSters = request.form.get('idConsultatie')
        if idConsultatieSters is not None:
            # am primit id-ul unei consultatii pentru sters
            cursor.execute("select prescriptieid from consultatii where consultatieid = " + str(idConsultatieSters))
            prescriptieID = cursor.fetchall()
            prescriptieID = prescriptieID[0][0]
            cursor.execute("DELETE FROM Consultatii WHERE consultatieid = " + str(idConsultatieSters))
            cursor.execute("delete from prescriptiimedicamente where prescriptieid = " + str(prescriptieID))
            cursor.execute("delete from prescriptii where prescriptieid = " + str(prescriptieID))
            conn.commit()


        receivedDate = request.form.get('searchData')

        if receivedDate is not None:
            # se efectueaza cautarea dupa an
            cursor.execute("select p.nume, p.prenume, d.nume, d.prenume, c.durata, c.detalii, c.data, c.consultatieid "
                           "from consultatii c inner join pacienti p on c.PacientID = p.PacientID inner join doctori "
                           "d on c.DoctorID = d.DoctorID where c.ConsultatieID in (select cc.consultatieid from "
                           "consultatii cc where year(cc.data) = " + str(receivedDate) + ") ")
        else:
            # se efectueaza cautarea dupa text
            formsData = request.form.get('searchText')
            if formsData is None:
                formsData = ''
            cursor.execute(
                "select p.nume, p.prenume, d.nume, d.prenume, c.durata, c.detalii, c.data, c.consultatieid from consultatii c inner join pacienti "
                "p on c.PacientID = p.PacientID inner join doctori d on c.DoctorID = d.DoctorID where p.nume like "
                "'%" + str(formsData) + "%' or p.prenume like '%" + str(formsData) + "%' or d.nume like '%" + str(
                    formsData) + "%' "
                                 "or d.prenume like '%" + str(formsData) + "%' order by c.data desc")


    else:
        # se extrag toti pacientii, fara a fi aplicat niciun filtru
        cursor.execute(
            "select p.nume, p.prenume, d.nume, d.prenume, c.durata, c.detalii, c.data, c.consultatieid from consultatii c inner join pacienti "
            "p on c.PacientID = p.PacientID inner join doctori d on c.DoctorID = d.DoctorID order by c.data desc")

    data = cursor.fetchall()

    dataToDisplay = formatData.formatToListOfDict(data, ['numePacient', 'prenumePacient', 'numeDoctor', 'prenumeDoctor',
                                                         'durata', 'detalii', 'data', 'id'])
    # formatam rezultatul query-ului sub forma de vector de dictionare

    prescriptii = []
    medicamente = []

    for consultatie in dataToDisplay:
        consultatieID = consultatie['id']
        # se extrag detaliile prescriptiei si numarul de medicamente pentru fiecare consultatie in parte
        cursor.execute("select distinct p.DetaliiPrescriptie, p.DurataTratament, count(distinct pm.MedicamentID) from Prescriptii p "
                       "left join Consultatii c on c.PrescriptieID = p.PrescriptieID left join "
                       "PrescriptiiMedicamente pm on p.PrescriptieID = pm.PrescriptieID where c.ConsultatieID = "
                       + str(consultatieID) + " group by p.DetaliiPrescriptie, p.DurataTratament")
        detaliiPrescriptie = cursor.fetchall()
        detaliiPrescriptie = formatData.formatToListOfDict(detaliiPrescriptie, ['detalii', 'durata', 'numarMedicamente'])
        # formatam rezultatul query-ului sub forma de vector de dictionare

        prescriptii.append(detaliiPrescriptie)

        # se extrag detaliile medicamentelor pentru fiecare consultatie in parte
        cursor.execute("select m.nume, m.Producator from Medicamente m inner join PrescriptiiMedicamente pm on "
                       "m.MedicamentID = pm.MedicamentID inner join Consultatii c on c.PrescriptieID = "
                       "pm.PrescriptieID where c.ConsultatieID = " + str(consultatieID))

        medicamenteConsultatie = cursor.fetchall()
        medicamenteConsultatie = formatData.formatToListOfDict(medicamenteConsultatie, ['nume', 'producator'])
        # formatam rezultatul query-ului sub forma de vector de dictionare

        medicamente.append(medicamenteConsultatie)
    #     se adauga medicamentele ce corespund consultatiei curente la vectorul de dictionare

    cursor.close()

    return render_template('consultatii.html', data=dataToDisplay, prescriptiiData=prescriptii, medicamenteData=medicamente, canDelete=stergere)


# pagina "Medicamente"
@app.route('/medicamente', methods=['POST', 'GET'])
def medicamente():
    cursor = conn.cursor()
    # se face legatura cu baza de date

    stergere = 0

    if request.method == 'POST':
        # am primit informatii de la un form
        pressed = request.form.get('toggleStergere')
        if pressed is not None:
            # se modifica optiunile de stergere
            stergere = request.form.get('delete')
            if stergere == 'DA':
                stergere = 1
            else:
                stergere = 0

        idMedicamentSters = request.form.get('idMedicament')
        if idMedicamentSters is not None:
            # se sterge medicamentul cu id-ul primit
            cursor.execute("DELETE FROM Medicamente WHERE medicamentid = " + str(idMedicamentSters))
            conn.commit()

        medicamentID = request.form.get('schimbaDisponibilitatea')
        if medicamentID is not None:
            # se schimba disponibilitatea medicamentului cu id-ul primit

            cursor.execute("select Disponibil from medicamente where medicamentid = " + str(medicamentID))
            disponibil = cursor.fetchall()
            disponibil = not disponibil[0][0]
            if disponibil == True:
                disp = 1
            else:
                disp = 0
            cursor.execute("update Medicamente set Disponibil = " + str(disp) + " where MedicamentID = " + str(medicamentID))

        nrAparitii = request.form.get('searchData')
        if nrAparitii is not None:
            # se efectueaza cautarea dupa numarul de aparitii in prescriptii
            cursor.execute("select m.medicamentid, m.nume, m.producator, m.substantaactiva, count(pm.medicamentid), "
                           "m.disponibil from medicamente m left join PrescriptiiMedicamente pm on m.MedicamentID = "
                           "pm.MedicamentID where m.MedicamentID in (select mm.medicamentid from medicamente mm left "
                           "join PrescriptiiMedicamente ppm on mm.MedicamentID = ppm.MedicamentID group by "
                           "mm.MedicamentID having count(ppm.medicamentid) = " + str(nrAparitii) + ") group by m.nume, m.Producator, "
                           "m.SubstantaActiva, m.disponibil, m.medicamentid")
        else:
            # se efectueaza cautarea dupa text
            formsData = request.form.get('searchText')
            if formsData is None:
                formsData = ''
            cursor.execute(
                "select m.medicamentid, m.nume, m.producator, m.substantaactiva, count(pm.medicamentid), m.disponibil from medicamente m left join "
                "PrescriptiiMedicamente pm on m.MedicamentID = pm.MedicamentID where m.nume like '%" + formsData + "%' "
                   "or m.producator like '%" + formsData + "%' or m.substantaactiva like '%" + formsData + "%' "
                   "group by m.nume, m.Producator, m.SubstantaActiva, m.disponibil, m.medicamentid")

    else:
        # se efectueaza extragerea nefiltrata a informatiilor despre medicamente
        cursor.execute(
            "select m.medicamentid, m.nume, m.producator, m.substantaactiva, count(pm.medicamentid), m.disponibil from medicamente m left join "
            "PrescriptiiMedicamente pm on m.MedicamentID = pm.MedicamentID group by m.nume, m.Producator, "
            "m.SubstantaActiva, m.disponibil, m.medicamentid")

    data = cursor.fetchall()
    cursor.close()
    dataToDisplay = formatData.formatToListOfDict(data, ['id', 'nume', 'producator', 'substantaActiva', 'numarAparitii', 'disponibil'])
    # formatam rezultatul query-ului sub forma de vector de dictionare

    return render_template('medicamente.html', data=dataToDisplay, canDelete=stergere)


# pagina de adaugare a unei consultatii
@app.route('/consultatii/adaugare', methods=['POST', 'GET'])
def consultatii_adaugare():

    cursor = conn.cursor()
    # se face legatura la baza de date


    # se extrag informatiile despre pacienti, doctori si medicamente pentru a fi afisate in formularul de adaugare
    cursor.execute("select p.nume, p.prenume from pacienti p")
    pacienti = cursor.fetchall()
    pacienti = formatData.formatToListOfDict(pacienti, ['nume', 'prenume'])

    cursor.execute("select d.nume, d.prenume from doctori d")
    doctori = cursor.fetchall()
    doctori = formatData.formatToListOfDict(doctori, ['nume', 'prenume'])

    cursor.execute("select m.nume from medicamente m")
    medicamente = cursor.fetchall()
    medicamente = formatData.formatToListOfDict(medicamente, ['nume'])

    if request.method == 'POST':
        # s-a adaugat un pacient
        # se extrag informatiile primite
        numePrenumePacient = request.form.get('Pacient')
        numePrenumeDoctor = request.form.get('Doctor')
        durataConsultatie = request.form.get('durata')
        dataConsultatie = request.form.get('data')
        detaliiConsultatie = request.form.get('detaliiConsultatie')
        detaliiPrescriptie = request.form.get('detaliiPrescriptie')
        durataPrescriptie = request.form.get('durataPrescriptie')
        medicamentePrescriptie = []
        meds = []
        meds.append(request.form.get('med1'))
        meds.append(request.form.get('med2'))
        meds.append(request.form.get('med3'))


        for m in meds:
            # se adauga numele medicamentelor la vectorul de medicamente, daca acestea exista
            if m != '-':
                medicamentePrescriptie.append(m)


        # se sparg numele intregi ale pacientului, respectiv doctorului in nume si prenume
        numePacient = numePrenumePacient.split()[0]
        prenumePacient = numePrenumePacient.split()[1]
        numeDoctor = numePrenumeDoctor.split()[0]
        prenumeDoctor = numePrenumeDoctor.split()[1]

        cursor.execute("insert into prescriptii (duratatratament, detaliiprescriptie) values ('"
                       + str(durataPrescriptie) + "','" + str(detaliiPrescriptie) + "')")
    #     se insereaza prescriptia noua

        cursor.execute("select top 1 prescriptieid from prescriptii where duratatratament = '" + str(durataPrescriptie) + "' and detaliiprescriptie = '" + str(detaliiPrescriptie) + "'")
        prescriptieId = cursor.fetchall()
        # se extrage id-ul primit pentru prescriptia nou introdusa

        cursor.execute("select p.pacientid from pacienti p where p.nume = '" + str(numePacient) + "' and p.prenume = '" + str(prenumePacient) + "'")
        pacientId = cursor.fetchall()
        # se extrage id-ul pacientului, bazat pe nume si prenume

        cursor.execute("select d.doctorid from doctori d where d.nume = '" + str(numeDoctor) + "' and d.prenume = '" + str(prenumeDoctor) + "'")
        doctorId = cursor.fetchall()
        # se extrage id-ul doctorului, bazat pe nume si prenume


        cursor.execute("insert into consultatii (pacientid, durata, detalii, prescriptieid, doctorid, data) values (" + str(pacientId[0][0]) + "," + str(durataConsultatie) + ",'" + str(detaliiConsultatie) + "'," + str(prescriptieId[0][0]) + "," + str(doctorId[0][0]) + ", '" + str(dataConsultatie) + "')")
        # se insereaza consultatia noua

        for med in medicamentePrescriptie:
            # se face legatura intre prescriptia nou introdusa si medicamente
            cursor.execute("select medicamentid from medicamente where nume = '" + str(med) + "'")
            medicamentId = cursor.fetchall()
            cursor.execute("insert into prescriptiimedicamente (prescriptieid, medicamentid) values (" + str(prescriptieId[0][0]) + "," + str(medicamentId[0][0]) + ")")
            # se insereaza in PrescriptiiMedicamente
    cursor.close()

    conn.commit()

    return render_template('consultatii_adaugare.html', pacienti=pacienti, doctori=doctori, medicamente=medicamente)


# pagina de adaugare a unui pacient
@app.route('/pacienti/adaugare', methods=['POST', 'GET'])
def pacienti_adaugare():

    if request.method == 'POST':
        # s-au primit informatiile despre pacient

        cursor = conn.cursor()
        # se face legatura cu baza de date

        numePacient = request.form.get('numePacient')
        prenumePacient = request.form.get('prenumePacient')
        # se extrag numele si prenumele pacientului

        cursor.execute("insert into pacienti (Nume, Prenume) values ('" + str(numePacient) + "','" + str(prenumePacient) + "')")
        # se insereaza noul pacient in baza de date

        conn.commit()


    return render_template('pacienti_adaugare.html')


# pagina de adaugare a unui doctor
@app.route('/doctori/adaugare', methods=['POST', 'GET'])
def doctori_adaugare():

    if request.method == 'POST':
        # s-au primit informatii despre noul doctor

        cursor = conn.cursor()

        numeDoctor = request.form.get('numeDoctor')
        prenumeDoctor = request.form.get('prenumeDoctor')
        dataNasterii = request.form.get('dataNasterii')
        # se extrag informatiile despre doctor

        cursor.execute("insert into doctori (Nume, Prenume, Disponibil, Datanasterii) values ('" + str(numeDoctor) + "','" + str(prenumeDoctor) + "' ,1, '" + dataNasterii + "')")
        # se insereaza informatiile despre doctor in baza de date

        conn.commit()


    return render_template('doctori_adaugare.html')


# pagina de adaugare pentru un medicament
@app.route('/medicamente/adaugare', methods=['POST', 'GET'])
def medicamente_adaugare():

    if request.method == 'POST':
        # s-au primit informatiile despre noul medicament

        cursor = conn.cursor()
        # se face legatura cu baza de date

        nume = request.form.get('numeMedicament')
        producator = request.form.get('producatorMedicament')
        substantaActiva = request.form.get('substantaActiva')
        # se extrag informatiile primite

        cursor.execute("insert into medicamente (Nume, producator, substantaactiva, disponibil) values ('" + str(nume)
                       + "','" + str(producator) + "','" + str(substantaActiva) + "',1" + ")")
        # se insereaza in baza de date noul medicament

        conn.commit()

    return render_template('medicamente_adaugare.html')


# conexiunea cu MS SQL Server
# se efectueaza o singura data, la pornirea aplicatiei
conn = pyodbc.connect(Driver='{SQL Server}',
                      Server='DESKTOP-SGVGGTV\SQLEXPRESS',
                      Database='Clinica',
                      Trusted_Connection='yes')



