from decimal import *

from bs4 import BeautifulSoup
import PyPDF2

data = {}

vars = {
    'total_distance': "0",
    'previous_rem_fuel': "0",
}

def extract_navlog(): # takes in a string (html of page) and returns a list of all waypoints and corresponding data
    extracted = []
    
    with open('input.txt', 'r') as file:
        page = BeautifulSoup(file.read(), 'html.parser')
        table = page.find('table', class_="waypoint mt-10 show-borders text-centered condensed no-wrap")
        
        # loop through all the containers, stop when a container has a child: class='sub-header' (this is the start of the alternate table)
        for container in table.find_all('tbody',  class_ = 'dont-break-container'):
            if container.find('tr', class_= "sub-header"): break # stop looping at the end of the table

            data_row = container.find('tr', class_= "table-data-row")

            if data_row:
                if data_row.span: data_row.span.string = ""
                row = []
                for info in data_row.stripped_strings:
                    row.append(info)
                
                extracted.append(row)

        # also extract final reserve, alternate and block fuel from the header
        vars['final_res_fuel'] = page.find('td', class_="performance-metric reserve-fuel").span.string.split(" ")[0]
        vars['alt_fuel'] = page.find('td', class_="performance-metric alternate-fuel").span.string.split(" ")[0] 
        vars['block_fuel'] = page.find('td', class_="performance-metric block-fuel").span.string.split(" ")[0]
        # set previous rem fuel to block fuel
        vars["previous_rem_fuel"] = vars['block_fuel']

        vars["cruise_altitude"] = table.find_all(string="Altitude")
        print("------------UNFINISHED ALTITUDE FUEL FLONW THINGY ON LINE 41------------")

    return extracted

def insert_data(data_row, wpt_index, page_index): # inserts row of waypoint data into the data dict
    # waypoint name
    data["page" + str(page_index)]["waypoint" + str(wpt_index)] = data_row[0] 

    # wind vector and speed
    wind_dir, wind_spd = data_row[6].split("/")
    data["page" + str(page_index)]["wind_dir" + str(wpt_index-1)] = wind_dir
    data["page" + str(page_index)]["wind_spd" + str(wpt_index-1)] = wind_spd

    # Course and Heading
    wca_int = int(data_row[2]) - int(data_row[3])
    if wca_int < -180: wca_int += 360
    elif wca_int > 180: wca_int -= 360
    wca = "0"
    if wca_int < 0: wca = str(wca_int)
    else: wca = "+" + str(wca_int)
    data["page" + str(page_index)]["mag_track" + str(wpt_index-1)] = data_row[3]
    data["page" + str(page_index)]["mag_hdg" + str(wpt_index-1)] = data_row[2]
    data["page" + str(page_index)]["wca" + str(wpt_index-1)] = wca

    # TAS and GS
    data["page" + str(page_index)]["spd_tas" + str(wpt_index-1)] = data_row[8]
    data["page" + str(page_index)]["spd_gs" + str(wpt_index-1)] = data_row[9]

    # Leg distance and Total distance
    vars["total_distance"] = str(int(data_row[10]) + int(vars["total_distance"]))
    data["page" + str(page_index)]["dist_leg" + str(wpt_index-1)] = data_row[10]
    data["page" + str(page_index)]["dist_tot" + str(wpt_index-1)] = vars["total_distance"]

    # Leg time and Total time
    data["page" + str(page_index)]["time_ete" + str(wpt_index-1)] = data_row[14]
    data["page" + str(page_index)]["time_tot" + str(wpt_index-1)] = data_row[16]

    # Leg Fuel and Remaining Fuel
    fuel_rem = data_row[13]
    leg_fuel = str(Decimal(vars["previous_rem_fuel"]) - Decimal(fuel_rem))
    vars["previous_rem_fuel"] = fuel_rem
    data["page" + str(page_index)]["fuel_leg" + str(wpt_index-1)] = leg_fuel
    data["page" + str(page_index)]["fuel_rem" + str(wpt_index-1)] = fuel_rem


def save_output_file():
    page = PyPDF2.PdfReader("OFP_Template.pdf").pages[0]

    # insert all data
    for index, page_key in enumerate(data):
        writer = PyPDF2.PdfWriter()
        writer.add_page(page)
        writer.update_page_form_field_values(writer.pages[0], data[page_key])

        # save output file
        with open(f"output/page {index}.pdf", "wb") as output_stream:
            writer.write(output_stream)

def remove_toc_tod(data_table): # loop through the data table to remove -TOC-, -TOD-
    new_table = []

    for i, row in enumerate(data_table):
        if row[0] == "-TOC-" or row[0] == "-TOD-":
            data_table[i+1][10] = str(int(data_table[i][10]) + int(data_table[i+1][10])) # Distance
            data_table[i+1][12] = str(Decimal(data_table[i][12]) + Decimal(data_table[i+1][12])) # Fuel

            cur_hrs, cur_min = data_table[i][14].split(":")
            next_hrs, next_min = data_table[i+1][14].split(":")
            new_hrs = int(cur_hrs) + int(next_hrs)
            new_min = int(cur_min) + int(next_min)
            if new_min > 60: new_min -= 60; new_hrs += 1
            new_min = "0" + str(new_min) if new_min < 10 else str(new_min)
            data_table[i+1][14] = str(new_hrs) + ":" + new_min # Time
        else:
            new_table.append(row)
    
    return new_table

def main(): # loop through all waypoints to insert data into the correct format
    data_table = extract_navlog()

    first_row = data_table[0]
    first_waypoint = first_row[0] # setup initial waypoint (usually ENGK)
    data_table = data_table[1:] # then remove the first waypoint (because there is no other info to get from row1)

    data_table = remove_toc_tod(data_table)

    waypoint_index = 2
    page_index = 1
    
    for waypoint in data_table:
        if waypoint_index == 2:
            # place only the waypoint name in wpt1
            data["page" + str(page_index)] = {}
            data["page" + str(page_index)]["waypoint1"] = first_waypoint
        
        insert_data(waypoint, waypoint_index, page_index)

        if waypoint_index == 16:
            # set the current waypoint to the first one for the next page
            first_waypoint = waypoint[0]
            #reset wpt_index to 0 and add 1 to page index
            waypoint_index = 1
            page_index += 1
        
        waypoint_index += 1
    
    # now loop through all waypoints backwards to calculate minimum remaining fuel
    min_remaining_fuel = Decimal(vars['final_res_fuel']) + Decimal(vars['alt_fuel'])
    for data_row in reversed(data_table):
        waypoint_index -= 1
        if waypoint_index <= 1: 
            waypoint_index = 16
            page_index -= 1

        data["page" + str(page_index)]["fuel_min" + str(waypoint_index-1)] = str(min_remaining_fuel)
        min_remaining_fuel += Decimal(data["page" + str(page_index)]["fuel_leg" + str(waypoint_index-1)])

    # Save the totals (for bottom of page)
    last_waypoint = data_table[-1]
    data["page1"]["total_fuel_on_board"] = vars['block_fuel'] + "G"
    data["page1"]["dist_total"] = first_row[10]
    data["page1"]["time_total"] = first_row[14]
    data["page1"]["fuel_total"] = last_waypoint[12] + "G"

print("--Processing--")
main()
print("--Saving--")
save_output_file()


#------------------TODO-----------------------
#  Detect when Full stop, Create new page from there on out
#  Automatically select FF for cruising altitude (Cruise altitude can be found bottom of Foreflight navlog)
#  Fuel calculations but put them in the second page of the navlog

#------------------ISSUES-----------------------
#  Min Remaining Fuel is wrong?

#------------------REQUIRES TESTING-----------------------