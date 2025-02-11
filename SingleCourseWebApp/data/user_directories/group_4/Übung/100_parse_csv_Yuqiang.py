'''Änderungen von Yuqiang 16.10.2023
   Sie finden es in Zeile 52, 239'''

import csv
import turtle
from pathlib import Path
import matplotlib.pyplot as plt

"""
Additional debug infos during run time (switch)
DEBUG_INFO can be False (no debug info), True (standard debug info) or 
any number greater than 1 to show extended debug infos
"""
DEBUG_INFO = False
GRAPH_MODE = 'Matplotlib' # Switch btw 'Turtle' and 'Matplotlib' 

header_a = []   # Array of header values
alldata = []    # Matrix (array of arrays) of csv data entries
header_index = {} # Header Index Dictionary
header_dict = {} # Header Dictionary


"""
Reading and parsing of CSV file containing all data
Please make sure that all float numbers are in US format in this file. 
Change German to US float format manually if needed in the CSV or Excel file!
You can do so, using following excel option: https://www.tippscout.de/excel-punkt-statt-komma.html
"""
def read_csv_file(filename):
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        rownum = 1
        header_a = []
        for row in reader:
            if rownum == 1: 
                header = row[0]
                header_a = header.split(";")
                if DEBUG_INFO == 2:
                    print("Header/rownum:", rownum, end=" : \"")
                    print(header, "\" -> ", header_a)
            else:
                data = row[0]
                data_a = data.split(";")
                if DEBUG_INFO == 2: 
                    print("Data/rownum: ", rownum, end=" : \"")
                    print(data, "\" -> ", data_a)
                alldata.append(data_a)
            rownum += 1

    return header_a, alldata

# Änderung: 3 Zeile Code gelöscht
def get_index(header_a, search_term='Liefermenge'):
    #i = 0 (Diese Zeile ist übrig)
    for i in range(len(header_a)):
        if header_a[i] == search_term:
            break
    #if i == 0: (wenn i == 0 d.h. Benutzer möchten 'Produktmenge anschauen')
    #    raise Exception("Die Kopfzeile scheint nicht zu existieren.")
    header_index[search_term] = i
    return header_index


def create_header_dict(header_a):
    for i in range(len(header_a)):
        header_dict[header_a[i]] = i
    return header_dict


def german_to_english_float(germfloat_string):
    if DEBUG_INFO > 1: print("germfloat before transform: ", germfloat_string)
    if "." in germfloat_string: germfloat_string = germfloat_string.replace(".", "")
    if "," in germfloat_string: germfloat_string = germfloat_string.replace(",", ".")
    if DEBUG_INFO > 1: print("germfloat after transform: ", germfloat_string)
    return germfloat_string


def calc_mean_by_index(alldata, search_term='Liefermenge'):
    mean = 0
    # len(alldata) gibt uns die Anzahl der Zeilen in der CSV-Datei
    num_rows = len(alldata)
    if DEBUG_INFO == 3: print("num_rows", num_rows)
    # header_index[search_term] liefert den Index für den gesuchten Term
    index = header_index[search_term]
    if DEBUG_INFO == 3: print("index: ", index)
    # Wir müssen über alle Zeilen der CSV-Datei suchen: alldata[i]
    # Und dort nach Werten suchen, die dem Index für den gesuchten Term entsprechen: float(alldata[i][index]
    for i in range(num_rows):
        # engfloat = german_to_english_float(alldata[i][index]) # is not needed if data is already in US float format
        if DEBUG_INFO == 3: 
            # print("alldata[",i,"]: ", alldata[i])
            print("alldata[",i,"][",index,"]: ", alldata[i][index], " -> ", alldata[i][index])
        mean += float(alldata[i][index])
    # Der Durchschnitt ist die Summe aller Werte geteilt durch die Anzahl an Zeilen num_rows
    mean /= num_rows
    
    # Dieser Durchschnitt wird per return als Ausgabewert der Funktion übergeben
    return mean


def calc_weighted_mean_by_index(min, alldata, search_term='Liefermenge'):
    # Der gewichtete Durchschnitt summiert lediglich über solche Werte, die über dem Minimum liegen
    # Ansonsten erfolgt die Berechnung des Durchschnitts analog zu calc_mean_by_index()
    mean = 0
    added_values = 0
    num_rows = len(alldata)
    if DEBUG_INFO == 3: print("num_rows", num_rows)
    index = header_index[search_term]
    if DEBUG_INFO == 3: print("index: ", index)
    for i in range(num_rows):
        # engfloat = german_to_english_float(alldata[i][index]) # is not needed if data is already in US float format
        if float(alldata[i][index]) > min:
            mean += float(alldata[i][index])
            added_values += 1
            if DEBUG_INFO == 3: 
                # print("alldata[",i,"]: ", alldata[i])
                print(added_values, ": alldata[",i,"][",index,"]: ", alldata[i][index], " -> ", alldata[i][index], "\tmean: ", mean)
    
    mean /= added_values
    
    return mean

def weighted_sum(alldata, prod_gruppe='101', search_term='Produktgruppe'):
    sum = 0
    # len(alldata) gibt uns die Anzahl der Zeilen in der CSV-Datei
    num_rows = len(alldata)
    # header_index[search_term] liefert der Index für den gesuchten Term
    index = header_index[search_term]
    # header_dict['Wert'] liefert einen zweiten Index für 'Wert' (index_wert)
    index_wert = header_dict['Wert']
    if DEBUG_INFO == 3: print("index: ", index, ", index_wert: ", index_wert)
    # Wir müssen über alle Zeilen der CSV-Datei suchen: alldata[i]
    # Und dort nach Werten suchen, die dem Index für den gesuchten Term entsprechen: float(alldata[i][index]
    for i in range(num_rows):
        if alldata[i][index] == prod_gruppe:
            # engfloat = german_to_english_float(alldata[i][index_wert]) # is not needed if data is already in US float format
            if DEBUG_INFO == 3: 
                print("alldata[",i,"][",index_wert,"]: ", alldata[i][index_wert], " -> ", alldata[i][index_wert])
            sum += float(alldata[i][index_wert])
    
    # Die Summe der entsprechenden Werte wird per return als Ausgabewert der Funktion übergeben
    return sum

# Generell blockgraph definitions
def draw_turtle_bar(t, height):
    """ Get turtle t to draw one bar, of height. """
    t.begin_fill()           # Added this line
    t.left(90)
    t.forward(height)
    t.write("  "+ str(height))
    t.right(90)
    t.forward(40)
    t.right(90)
    t.forward(height)
    t.left(90)
    t.end_fill()             # Added this line
    t.forward(10)

# Draw CSV values to graph 
# in form of a simple turtle graph
def draw_turtle_graph(alldata, search_term='Liefermenge'):
    wn = turtle.Screen()         # Set up the window and its attributes
    wn.bgcolor("lightgreen")

    tess = turtle.Turtle()       # Create tess and set some attributes
    tess.color("blue", "red")
    tess.pensize(3)
    # tbd: set initial position to farmost left bottom corner

    turtle_array = []
    num_rows = len(alldata)
    if DEBUG_INFO == 4: print("num_rows", num_rows)
    # header_index[search_term] liefert der Index für den gesuchten Term
    index = header_index[search_term]
    if DEBUG_INFO == 4: print("index: ", index)
    # Wir müssen über alle Zeilen der CSV-Datei suchen: alldata[i]
    # Und dort nach Werten suchen, die dem Index für den gesuchten Term entsprechen: float(alldata[i][index]
    for i in range(num_rows):
        if DEBUG_INFO == 4: 
            print("alldata[",i,"]: ", alldata[i])
            print("alldata[",i,"][",index,"]: ", float(alldata[i][index]))
        turtle_array.append(float(alldata[i][index]))
    print("turtle array: ", turtle_array)
    
    for a in turtle_array:
        draw_turtle_bar(tess, a)

    wn.mainloop()


# Draw CSV values to graph 
# in form of a matplotlib bar graph
def draw_graph(alldata, search_term='Liefermenge'):
    plot_dict = {}
    num_rows = len(alldata)
    if DEBUG_INFO == 4: print("num_rows", num_rows)
    # header_index[search_term] liefert der Index für den gesuchten Term
    index = header_index[search_term]
    if DEBUG_INFO == 4: print("index: ", index)
    # Wir müssen über alle Zeilen der CSV-Datei suchen: alldata[i]
    # Und dort nach Werten suchen, die dem Index für den gesuchten Term entsprechen: float(alldata[i][index]
    # (vgl. draw_turtle_graph())
    # In plot_dict[i] sammeln wir schließlich sämtliche gefundene Werte: plot_dict[i] = float(alldata[i][index])
    # Für die graph. Ausgabe eines Balkendiagramms mit matplotlib benötigen wir sowohl für die
    # x- als auch y-Achse Listen (arrays). Diese gewinnen wir aus dem dictionary plot_dict mit Hilfe von
    # x_axis_array = list(plot_dict.keys()) sowie für die y-Achse analog. Diese Array können wir für die zu 
    # findende plot-Funktion von matplotlib verwenden.

    for i in range(num_rows):
        if DEBUG_INFO == 4: 
            print("alldata[",i,"]: ", alldata[i])
            print("alldata[",i,"][",index,"]: ", float(alldata[i][index]))
        plot_dict[i] = float(alldata[i][index])

    if DEBUG_INFO == 4: print(f"plot_dict: {plot_dict}")
    x_axis_array = list(plot_dict.keys())
    y_axis_array = list(plot_dict.values())
    if DEBUG_INFO == 4: print(f"x_axis_array: {x_axis_array}, y_axis_array: {y_axis_array}")
    plt.bar(x_axis_array, y_axis_array)
    plt.xticks(rotation='vertical')
    plt.ylabel(search_term)
    plt.show()


# __main__
# Einlesen und Parsen der CSV-Datei von filename
data_folder = Path(r"C:\Users\wiw\Desktop\Python-Projekte")
filename = data_folder / "100_Pivot_Grunddaten.csv"
header_a, alldata = read_csv_file(filename)
header_dict = create_header_dict(header_a)

if DEBUG_INFO: 
    print("--- Start debug infos ---")
    print("Kopfzeile (header_a): ", header_a)
    print("... header_dict: ", header_dict)
    print("Datenzeilen (alldata): ", alldata)
    print("--- End debug infos ---")

#Änderung: wenn man ungültige Zahl eingibt, zeigt eine Fehlermeldung an
while True:
    try:
        search_nr = int(input("""Welchen der folgenden Terme wollen Sie untersuchen?
        1: (gew.) Durchschnitt von Bestellmenge
        2: (gew.) Durchschnitt von Liefermenge 
        3: (gew.) Durchschnitt von Wert 
        4: gew. Summe von Produktgruppe
        9: Exit 
        >>> """))
    except:
        print("Bitte korrekte Zahl eingeben!")
        break
    else:
        if search_nr == 1:
            search_term = 'Bestellmenge'
        elif search_nr == 2:
            search_term = 'Liefermenge'
        elif search_nr == 3:
            search_term = 'Wert'
        elif search_nr == 4:
            search_term = 'Produktgruppe'
        elif search_nr == 9:
            break
        else:
            print("Bitte richtige Zahl (1 bis 4 order 9) eingeben!")
            break

    # Welche Index-Nummer hat der gesuchte Term innerhalb der CSV-Datei
    header_index = get_index(header_a, search_term)

    if search_nr in (1, 2, 3):
        # a. Berechnung und Ausgabe des Mittelwerts für alle Werte des gesuchten Terms
        # Optimierungsmöglichkiet: weighted_mean = calc_weighted_mean_by_index(0, alldata, search_term)
        # Hierdurch kann calc_mean_by_index() wegfallen!
        mean = calc_mean_by_index(alldata, search_term)
        print("Durchschnittliche {0}: {1:6.2f}".format(search_term, mean))

        # b. Berechnung und Ausgabe des gewichteten Mittelwerts für alle Werte des gesuchten Terms
        # tbd: falsche Eingaben abfangen
        try:
            min = int(input("Geben Sie ein Minimum zur Berechnung des gew. MW ein: "))
        except:
            print("Bitte eine Zahl eingeben!")
            break
        else: 
            if min <= 0:
                print("Das Minimum muss größer als 0 sein. Setze Minimum auf 400!")
                min = 400 # setting default value

        # weighted_mean = calc_weighted_mean_by_index(min, alldata, search_term='Liefermenge')
        weighted_mean = calc_weighted_mean_by_index(min, alldata, search_term)
        print("Gewichtete durchschnittliche {0} für min: {1:6.2f} = {2:6.2f}".format(search_term, min, weighted_mean))

        # c. Graph zeichnen
        if input("Zugehörigen Graph zeichnen (y/n)? ") == "y":
            print(f"Starting drawing {GRAPH_MODE} graph ...")
            if GRAPH_MODE == 'Turtle':
                draw_turtle_graph(alldata, search_term)
            else:
                # Matplotlib bar graph as standard
                draw_graph(alldata, search_term)

    elif search_nr == 4:
        # Summe aller Werte für eine gesuchte Produktgruppe 
        prod_gruppe = input("Welchen Produktnummer wollen Sie untersuchen? (101, 199, 201, etc.) ")
        # Alternative function invocation: sum = weighted_sum(alldata, '199', 'Produktgruppe')
        sum = weighted_sum(alldata, prod_gruppe='101', search_term='Produktgruppe')
        print("Summe aller Werte für Produktnummer {0}: {1:6.2f}".format(prod_gruppe, sum))

    print("\n---------------------\n")