from flask import Flask, request, redirect, render_template, session, url_for, flash, session, jsonify, make_response
import pymysql
from flask_mysqldb import MySQL

# Need to have html pages inside "templates" folder. this is an
# assumption that Flask makes

#change to reflect whatever your server/sql reqs are
# db = pymysql.connect(host ="localhost",
#                      user = "root",
#                      password = "gatech",
#                      database = "buzz_cars")

# app = Flask(__name__)

# USER_TYPE = 'DEFAULT'

app = Flask(__name__)

app.secret_key = "super secret key"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'gatech'
app.config['MYSQL_DB'] = 'buzz_cars'

mysql = MySQL(app)


#still needs constraints 
#adding colors might not be working the way it should yet
@app.route('/add_vehicle', methods = ["GET", "POST"])
def add_vehicle():
    if request.method == 'GET':
        search_customerID = request.args.get('search_customerID')
        # search_customerID = customerSEARCH['search_customerID']
        cur = mysql.connection.cursor()
        q_customer = '''SELECT  
                    C.customerID,
                    IFNULL(I.individual_name, B.business_name) as customer,
                    C.email, C.phone_number,
                    C.street, C.city, C.state, C.zip_code
                FROM customer C
                LEFT JOIN
                    (SELECT CONCAT(first_name, ' ', last_name) as individual_name, 
                            customerID
                            FROM individual )I on I.customerID = C.customerID
                LEFT JOIN 
                    (SELECT business_name, customerID
                    FROM business) B on B.customerID = C.customerID
                WHERE C.customerID = '{0}'; '''.format(search_customerID)
        result = cur.execute(q_customer)
        if result > 0:
            customer_info = cur.fetchall()
            return render_template('add_vehicle.html', customer_info = customer_info)
        else:
            return render_template('add_vehicle.html')

    if request.method =='POST':

        vehicleADD = request.form
        cur = mysql.connection.cursor()
        q = '''
        select
        vin
        from vehicle;
        '''
        results = cur.execute(q)
        result = cur.fetchall()
        cur.close()
        db_cars = [item[0] for item in result]
        
        cur = mysql.connection.cursor()
        q_1 = '''
        select
        customerID
        from customer;
        '''
        cur.execute(q_1)
        ids = cur.fetchall()
        cur.close()
        db_customers = [id[0] for id in ids]
        
        # print(vehicleADD['vin'])
        # print(db_cars)
        if vehicleADD['vin'] in db_cars:
            flash('Vehicle not added: already in inventory or customer not in database', 'warning')
            return  render_template('add_vehicle.html')
        
        elif vehicleADD["purchased_from_customer"] not in db_customers:
            flash('Vehicle not added: already in inventory or customer not in database', 'warning')
            return  render_template('add_vehicle.html')
        else:
            vin = vehicleADD['vin']
            model_name = vehicleADD['model_name']
            year = vehicleADD['year']
            description = vehicleADD['description']
            manufacturer_name = vehicleADD['manufacturer_name']
            condition_value = vehicleADD["condition_value"]
            vehicle_type = vehicleADD["vehicle_type"]
            odometer = vehicleADD["odometer"]
            fuel_type = vehicleADD["fuel_type"]
            # colors = vehicleADD["colors"]
            colors = request.form.getlist('colors')
            purchase_date = vehicleADD["purchase_date"]
            purchase_price = vehicleADD["purchase_price"]
            purchased_from_customer = vehicleADD["purchased_from_customer"]
            purchase_clerk = vehicleADD["purchase_clerk"]                        
            
            #getting manufactuer ID
            cur = mysql.connection.cursor()
            cur.execute( '''SELECT manufacturerID FROM manufacturer
                                WHERE manufacturer_name = '{0}'; '''.format(manufacturer_name))
            manufacturerID = cur.fetchall()
            cur.close()
            
            #getting fuel type ID
            cur = mysql.connection.cursor()            
            cur.execute( '''SELECT fueltypeID FROM fueltype
                                WHERE fuel_type_name = '{0}'; '''.format(fuel_type))
            fueltypeID = cur.fetchall()
            cur.close()
            
            #getting condition ID
            cur = mysql.connection.cursor()
            cur.execute( '''SELECT conditionID FROM vehiclecondition 
                                WHERE v_condition = '{0}'; '''.format(condition_value))
            conditionID = cur.fetchall()
            cur.close()
            
            #getting vehicle type ID
            cur = mysql.connection.cursor() 
            cur.execute( '''SELECT vehicletypeID FROM vehicletype
                                WHERE type = '{0}'; '''.format(vehicle_type)) 
            vehicletypeID = cur.fetchall()
            cur.close()
            
            #getting color IDs
            # cur = db.cursor()   
            # cur.execute( ''' SELECT colorID FROM color 
            #                     WHERE color_name LIKE '{0}' '''.format(colors))
            # cur.execute('''SELECT group_concat(color_name) FROM color WHERE colorID in ({0})'''.format('colors'))
            # colorID = cur.fetchall()
            # cur.close()
            
            # color_str = str(colors[0]) + ',' + str(colors[1])
            
            color_str = ','.join(colors)
                

            
            #saleID attempt
            cur = mysql.connection.cursor()
            cur.execute(''' SELECT (MAX(purchaseID)+1) FROM purchasetransaction;''')
            purchaseID = cur.fetchall()
            # purcaseID = purchaseID + 1

            try:
                q_vehicle = '''INSERT INTO vehicle
                            (vin, model, year, description, manufacturerID, 
                            conditionID, vehicletypeID, mileage, fueltypeID, colorIDs) 
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)  '''
            except Exception as e:
                print(f"Unexpected error: {e}")
                return render_template(url_for('add_vehicle'))


            # how to add purchaseID below?
            q_purchasetransaction = '''INSERT INTO purchasetransaction
                        (purchaseID , customerID, username, vin, purchase_date, purchase_price)
                        VALUES(%s, %s, %s, %s, %s, %s)'''
                        
            cur = mysql.connection.cursor()
            cur.execute(q_vehicle, (vin, model_name, year, description, manufacturerID, conditionID, vehicletypeID, odometer, fueltypeID, color_str))
            cur.execute(q_purchasetransaction, (purchaseID, purchased_from_customer, purchase_clerk, vin, purchase_date, purchase_price))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('search_vehicle'))
    return render_template('add_vehicle.html', customer_info = customer_info)


#working, but need to connect it to page with "search customer"
@app.route('/add_individual', methods =['GET', 'POST'])
def add_individual():
    if request.method =='POST':
        individualADD = request.form
        customerID = individualADD["driver_license_id"]
        driver_license_id = individualADD["driver_license_id"]
        first_name = individualADD["first_name"]
        last_name = individualADD["last_name"]
        phone_number = individualADD["phone_number"]
        email = individualADD["email"]
        street = individualADD["street"]
        city = individualADD["city"]
        state = individualADD["state"]
        zip_code = individualADD["zip_code"]
        
        cur = mysql.connection.cursor()
        cur.execute('''SELECT customerID from customer;''')
        ids = cur.fetchall()
        cur.close()
        db_ids = [item[0] for item in ids]
        if customerID in db_ids:
            flash('Customer not added: already in database', 'warning')
            return  render_template('add_individual.html')
        else:
            q_customer = "INSERT INTO customer(customerID, phone_number, email, street, city, state, zip_code) VALUES(%s, %s, %s, %s, %s, %s, %s)"
            q_individual = "INSERT INTO individual(customerID, driver_license_id, first_name, last_name) VALUES(%s, %s, %s, %s)"
            
            cur = mysql.connection.cursor()
            cur.execute(q_customer, (customerID, phone_number, email, street, city, state, zip_code))
            cur.execute(q_individual, (customerID, driver_license_id, first_name, last_name))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('search_vehicle'))
    return render_template("add_individual.html")
    
    
#working, but need to connect it to page with "search customer"
@app.route('/add_business', methods =['GET', 'POST'])
def add_business():
    if request.method =='POST':
        businessADD = request.form
        customerID = businessADD["tax_id"]
        tax_id = businessADD["tax_id"]
        position = businessADD["position"]
        business_name = businessADD["business_name"]
        first_name = businessADD["first_name"]
        last_name = businessADD["last_name"]
        phone_number = businessADD["phone_number"]
        email = businessADD["email"]
        street = businessADD["street"]
        city = businessADD["city"]
        state = businessADD["state"]
        zip_code = businessADD["zip_code"]
        
        cur = mysql.connection.cursor()
        cur.execute('''SELECT customerID from customer;''')
        ids = cur.fetchall()
        cur.close()
        db_ids = [item[0] for item in ids]
        if customerID in db_ids:
            flash('Customer not added: already in database', 'warning')
            return  render_template('add_business.html')
        else:
            q_business = "INSERT INTO business(customerID, tax_id, position, business_name, first_name, last_name) VALUES(%s, %s, %s, %s, %s, %s)"
            q_customer = "INSERT INTO customer(customerID, phone_number, email, street, city, state, zip_code) VALUES(%s, %s, %s, %s, %s, %s, %s)"
            
            cur = mysql.connection.cursor()
            cur.execute(q_customer, (customerID, phone_number, email, street, city, state, zip_code))
            cur.execute(q_business, (customerID, tax_id, position, business_name, first_name, last_name))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('search_vehicle'))
    return render_template("add_business.html")


# working, but need to connect it to the page with "search_vendor"
@app.route('/add_vendor', methods =['GET', 'POST'])
def add_vendor():
    if request.method =='POST':
        vendorADD = request.form
        vendor_name = vendorADD["vendor_name"]
        phone = vendorADD["phone"]
        street = vendorADD["street"]
        city = vendorADD["city"]
        state = vendorADD["state"]
        zip_code = vendorADD["zip_code"]

        q_vendor = "INSERT INTO vendor(vendor_name, phone, street, city, state, zip_code) VALUES(%s, %s, %s, %s, %s, %s)"
        
        cur = mysql.connection.cursor()
        cur.execute(q_vendor, (vendor_name, phone, street, city, state, zip_code))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('search_vehicle'))
    return render_template("add_vendor.html")

# this is a page with buttons that lead to the individual reports
@app.route('/general_reports', methods=['GET', 'POST'])
def reports_buttons():
    if request.method == 'POST':
        # these will be used in the 'specific_monthly_sales" page
        year = request.form.get('year')
        month = request.form.get('month')
        return redirect(url_for(get_specific_monthly_sales, year = year, month = month))
    return render_template('skeleton_reports.html')


# working perfectly
@app.route('/reports_part_statistics', methods=['GET', 'POST'])
def get_part_stats():
    cur = mysql.connection.cursor()
    q = "SELECT vendor_name, SUM(quantity), ROUND(SUM(price),2) FROM partorder GROUP BY vendor_name"
    resultValue = cur.execute(q)
    if resultValue > 0:
        part_stats = cur.fetchall()
        cur.close()
        return render_template('part_stats.html', part_stats = part_stats)


# working perfectly
@app.route('/price_per_condition_report', methods=['POST', 'GET'])
def get_price_per_condition():
    cur = mysql.connection.cursor()
    q = '''SELECT type, VC.v_condition, ROUND(AVG(purchase_price), 2) 
    FROM vehicle V
    INNER JOIN vehicleType VT ON VT.vehicletypeID = V.vehicletypeID
    INNER JOIN vehiclecondition VC ON VC.conditionID = V.conditionID
    INNER JOIN
    purchasetransaction PT 
    on V.vin = PT.vin
    GROUP BY V.vehicletypeID, V.conditionID'''
    resultValue = cur.execute(q)
    if resultValue > 0:
        price_per_condition = cur.fetchall()
        cur.close()
        return render_template('price_per_condition.html', price_per_condition = price_per_condition)
    
    
# working perfectly
@app.route('/monthly_sales_report', methods=["GET", "POST"])
def get_monthly_sales():
    cur = mysql.connection.cursor()
    q = ''' SELECT YEAR(sale_date) as Year,
                MONTH(sale_date) as MONTH,
                COUNT(ST.vin) as total_sold, 
                ROUND(SUM((1.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Sales_Income, 
                ROUND(SUM((.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Net_Income 
            FROM salestransaction ST 
            INNER JOIN
            (SELECT partorder.vin, 
            SUM((partorder.quantity * partorder.price)) as Total_part FROM partorder GROUP BY partorder.vin) T ON ST.vin = T.vin
            INNER JOIN 
            purchasetransaction PT ON PT.vin = ST.vin
            GROUP BY YEAR(sale_date), MONTH(sale_date)
            ORDER BY YEAR(sale_date) DESC, MONTH(sale_date) DESC; '''    
    resultValue = cur.execute(q)
    if resultValue > 0:
        sales = cur.fetchall()
        cur.close()
    return render_template('monthly_sales.html', sales = sales)


# working perfectly
@app.route('/specific_monthly_sales', methods = ['GET', 'POST'])
def get_specific_monthly_sales():
    Year = request.args.get('year', None)
    Month = request.args.get('month', None)

    if Year != "" and Month != "":
            q ='''SELECT 
                    YEAR(ST.sale_date) as Year,
                    MONTH(ST.sale_date) as Month,
                    COUNT(ST.vin) as total_sold,
                    U.first_name,
                    U.last_name,
                    ROUND(SUM((1.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Sales_Income,
                    ROUND(SUM((.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Net_Income
                FROM salestransaction ST 
                LEFT JOIN 
                user U on ST.username = U.username
                INNER JOIN
                    (SELECT partorder.vin, 
                    SUM((partorder.quantity * partorder.price)) as Total_part 
                    FROM partorder 
                    GROUP BY partorder.vin) T ON ST.vin = T.vin
                    INNER JOIN 
                    purchasetransaction PT ON PT.vin = ST.vin
                WHERE YEAR(ST.sale_date) = '{0}' and MONTH(ST.sale_date) = '{1}'
                GROUP BY U.Username, Month
                ORDER BY total_sold DESC, Total_Sales_Income DESC; '''.format(Year, Month)
            cursor = mysql.connection.cursor()
            results = cursor.execute(q)
            yearly = cursor.fetchall()
            cursor.close()
            return render_template('specific_monthly_sales.html', yearly = yearly)
            
    if Year != "" and Month == "":
            q ='''SELECT 
                    YEAR(ST.sale_date) as Year,
                    MONTH(ST.sale_date) as Month,
                    COUNT(ST.vin) as total_sold,
                    U.first_name,
                    U.last_name,
                    ROUND(SUM((1.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Sales_Income,
                    ROUND(SUM((.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Net_Income
                FROM salestransaction ST 
                LEFT JOIN 
                user U on ST.username = U.username
                INNER JOIN
                    (SELECT partorder.vin, 
                    SUM((partorder.quantity * partorder.price)) as Total_part 
                    FROM partorder 
                    GROUP BY partorder.vin) T ON ST.vin = T.vin
                    INNER JOIN 
                    purchasetransaction PT ON PT.vin = ST.vin
                WHERE YEAR(ST.sale_date) = '{0}'
                GROUP BY U.username, Month
                ORDER BY total_sold DESC, Total_Sales_Income DESC; '''.format(Year)
            cursor = mysql.connection.cursor()
            results = cursor.execute(q)
            yearly = cursor.fetchall()
            cursor.close()
            return render_template('specific_monthly_sales.html', yearly = yearly)
    
    if Year == "" and Month != "":
            q ='''SELECT 
                    YEAR(ST.sale_date) as Year,
                    MONTH(ST.sale_date) as Month,
                    COUNT(ST.vin) as total_sold,
                    U.first_name,
                    U.last_name,
                    ROUND(SUM((1.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Sales_Income,
                    ROUND(SUM((.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Net_Income
                FROM salestransaction ST 
                LEFT JOIN 
                user U on ST.username = U.username
                INNER JOIN
                    (SELECT partorder.vin, 
                    SUM((partorder.quantity * partorder.price)) as Total_part 
                    FROM partorder 
                    GROUP BY partorder.vin) T ON ST.vin = T.vin
                    INNER JOIN 
                    purchasetransaction PT ON PT.vin = ST.vin
                WHERE MONTH(ST.sale_date) = '{0}'
                GROUP BY U.username, Month
                ORDER BY total_sold DESC, Total_Sales_Income DESC; '''.format(Month)
            cursor = mysql.connection.cursor()
            results = cursor.execute(q)
            yearly = cursor.fetchall()
            return render_template('specific_monthly_sales.html', yearly = yearly)
            
    if Year == "" and Month == "":
            q ='''SELECT 
                    YEAR(ST.sale_date) as Year,
                    MONTH(ST.sale_date) as Month,
                    COUNT(ST.vin) as total_sold,
                    U.first_name,
                    U.last_name,
                    ROUND(SUM((1.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Sales_Income,
                    ROUND(SUM((.25 * PT.purchase_price) + (1.1 * T.Total_part)),2) as Total_Net_Income
                FROM salestransaction ST 
                LEFT JOIN 
                user U on ST.username = U.username
                INNER JOIN
                    (SELECT partorder.vin, 
                    SUM((partorder.quantity * partorder.price)) as Total_part 
                    FROM partorder 
                    GROUP BY partorder.vin) T ON ST.vin = T.vin
                    INNER JOIN 
                    purchasetransaction PT ON PT.vin = ST.vin
                GROUP BY U.username, Month
                ORDER BY total_sold DESC, Total_Sales_Income DESC; '''
            cursor = mysql.connection.cursor()
            results = cursor.execute(q)
            yearly = cursor.fetchall()
            return render_template('specific_monthly_sales.html', yearly = yearly)


# working perfectly
@app.route('/time_in_inventory_report', methods=["GET", "POST"])
def get_avg_time_inventory():
    cur = mysql.connection.cursor()
    q = ''' SELECT 
                VT.type, 
	            IFNULL(ROUND(AVG(datediff(IFNULL(ST.sale_date,0), PT.purchase_date) + 1),0), 'N/A') as average_time
            FROM vehicle V
            LEFT JOIN vehicletype VT on VT.vehicletypeID = V.vehicletypeID
            LEFT JOIN purchasetransaction PT on PT.vin = V.vin
            LEFT JOIN salestransaction ST on ST.vin = V.vin
            GROUP BY V.vehicletypeID;'''
    resultValue = cur.execute(q)
    if resultValue > 0:
        time_in_inv = cur.fetchall()
        cur.close()
    return render_template('time_in_inventory.html', time_in_inv = time_in_inv)


# works aside from not knowing how to highlight rows where # parts needed > 5 or avg cost of parts > $500
@app.route('/seller_history_report', methods=["GET", "POST"])
def get_seller_history():
    cur = mysql.connection.cursor()
    sql_mode_query = "SET SESSION sql_mode = ''"
    cur.execute(sql_mode_query)
    mysql.connection.commit()
    cur.close()

    cur = mysql.connection.cursor()
    q = ''' 
            
            SELECT 
                IFNULL(I.individual_name, B.business_name) as customer, 
	            COUNT(PT.vin) as total_number_cars, 
                ROUND(AVG(PT.purchase_price),2) as avg_vehicle_price,
                IFNULL(number_parts,0) as total_num_parts,
                ROUND(IFNULL(total_part_price,0),2) as total_parts_cost
            FROM purchasetransaction PT
            LEFT JOIN
                (SELECT PO.vin, COUNT(PO.vin) as number_parts, SUM(PO.price) as total_part_price
            FROM partorder PO
            GROUP BY PO.vin) P on PT.vin = P.vin
            LEFT JOIN
                (SELECT CONCAT(first_name, ' ', last_name) as individual_name, customerID
            FROM individual) I on I.customerID = PT.customerID
            LEFT JOIN
                (SELECT business_name, customerID
                FROM business) B on B.customerID = PT.customerID
            GROUP BY PT.customerID
            ORDER BY total_number_cars DESC, avg_vehicle_price DESC; ''' 
    resultValue = cur.execute(q)
    # print(resultValue)
    if resultValue > 0:
        history = cur.fetchall()
        cur.close()
        # print(history)
    return render_template('seller_history.html', history = history)


############# JUSTINES STUFF ##############


@app.route('/', methods=['GET','POST'])
def search_vehicle():
    if request.method == 'POST':
        vehicleType = request.form.get('vehicleType')
        modelYear = request.form.get('modelYear')
        manufacturer = request.form.get('manufacturer')
        fuelType = request.form.get('fuelType')
        colors = request.form.get('color')
        salesPrice = request.form.get('salesPrice')
        keyword = request.form.get('keyword')
        vin = request.form.get('vin')
        filterSold = request.form.get('filterSold')
        flag = False

        query = ''

        userrole = request.cookies.get('userrole')

        if userrole in ['Manager', 'Owner']: 

            if filterSold == 'sold':
                query = '''SELECT manufacturer_name, V.vin, model, year, fuel_type_name, GROUP_CONCAT(color_name), mileage, ROUND(PT.purchase_price * 1.25 + T.total, 2)
                        FROM VEHICLE V, color C, fuelType FT, manufacturer M, vehicleType VT, PurchaseTransaction PT, SalesTransaction ST, (
                                        SELECT PT.vin, (coalesce(part_price, 0)) as total from PurchaseTransaction PT
                                        LEFT OUTER JOIN (SELECT PO.vin, SUM(quantity * price) * 1.1 as part_price, SUM(CASE WHEN statusID!='installed' THEN 1 ELSE 0 END) as remove 
                                                        FROM PartOrder PO 
                                                        GROUP BY vin) 
                                        PO ON PO.vin = PT.vin WHERE (PO.remove = 0 or PO.remove is NULL) GROUP BY vin) T
                        WHERE FT.fueltypeid = v.fueltypeid
                        AND V.manufacturerID = M.manufacturerID
                        AND VT.vehicletypeID = V.vehicletypeID
                        AND T.vin = V.vin
                        AND PT.vin = V.vin
                        AND ST.vin = V.vin
                        AND FIND_IN_SET(colorId, colorids)'''
            
            elif filterSold == 'unsold':
                query = '''SELECT manufacturer_name, V.vin, model, year, fuel_type_name, GROUP_CONCAT(color_name), mileage, ROUND(PT.purchase_price * 1.25 + T.total, 2)
                        FROM VEHICLE V, color C, fuelType FT, manufacturer M, vehicleType VT, PurchaseTransaction PT, (
                                        SELECT PT.vin, (coalesce(part_price, 0)) as total from PurchaseTransaction PT
                                        LEFT OUTER JOIN (SELECT PO.vin, SUM(quantity * price) * 1.1 as part_price FROM PartOrder PO GROUP BY vin) 
                                        PO ON PO.vin = PT.vin GROUP BY vin) T
                        WHERE FT.fueltypeid = v.fueltypeid
                        AND V.manufacturerID = M.manufacturerID
                        AND VT.vehicletypeID = V.vehicletypeID
                        AND T.vin = V.vin
                        AND PT.vin = V.vin
                        AND NOT EXISTS (SELECT * FROM SalesTransaction ST WHERE ST.vin = V.vin)
                        AND FIND_IN_SET(colorId, colorids)'''
            else:
                query = '''SELECT manufacturer_name, V.vin, model, year, fuel_type_name, GROUP_CONCAT(color_name), mileage, ROUND(PT.purchase_price * 1.25 + T.total, 2)
                            FROM VEHICLE V, color C, fuelType FT, manufacturer M, vehicleType VT, PurchaseTransaction PT, (
                                            SELECT PT.vin, (coalesce(part_price, 0)) as total from PurchaseTransaction PT
                                            LEFT OUTER JOIN (SELECT PO.vin, SUM(quantity * price) * 1.1 as part_price FROM PartOrder PO GROUP BY vin) 
                                            PO ON PO.vin = PT.vin GROUP BY vin) T
                            WHERE FT.fueltypeid = v.fueltypeid
                            AND V.manufacturerID = M.manufacturerID
                            AND VT.vehicletypeID = V.vehicletypeID
                            AND T.vin = V.vin
                            AND PT.vin = V.vin
                            AND FIND_IN_SET(colorId, colorids)'''
                            
        elif userrole == 'Inventory Clerk':
            query = '''SELECT manufacturer_name, V.vin, model, year, fuel_type_name, GROUP_CONCAT(color_name), mileage, ROUND(PT.purchase_price * 1.25 + T.total, 2)
                        FROM VEHICLE V, color C, fuelType FT, manufacturer M, vehicleType VT, PurchaseTransaction PT, (
                                        SELECT PT.vin, (coalesce(part_price, 0)) as total from PurchaseTransaction PT
                                        LEFT OUTER JOIN (SELECT PO.vin, SUM(quantity * price) * 1.1 as part_price FROM PartOrder PO GROUP BY vin) 
                                        PO ON PO.vin = PT.vin GROUP BY vin) T
                        WHERE FT.fueltypeid = v.fueltypeid
                        AND V.manufacturerID = M.manufacturerID
                        AND VT.vehicletypeID = V.vehicletypeID
                        AND T.vin = V.vin
                        AND PT.vin = V.vin
                        AND NOT EXISTS (SELECT * FROM SalesTransaction ST WHERE ST.vin = V.vin)
                        AND FIND_IN_SET(colorId, colorids)'''
            
            
        
        else: 

            query = '''SELECT manufacturer_name, V.vin, model, year, fuel_type_name, GROUP_CONCAT(color_name), mileage, ROUND(PT.purchase_price * 1.25 + T.total, 2)
                        FROM VEHICLE V, color C, fuelType FT, manufacturer M, vehicleType VT, PurchaseTransaction PT, (
                                        SELECT PT.vin, (coalesce(part_price, 0)) as total from PurchaseTransaction PT
                                        LEFT OUTER JOIN (SELECT PO.vin, SUM(quantity * price) * 1.1 as part_price, SUM(CASE WHEN statusID!='installed' THEN 1 ELSE 0 END) as remove 
                                                        FROM PartOrder PO 
                                                        GROUP BY vin) 
                                        PO ON PO.vin = PT.vin WHERE (PO.remove = 0 or PO.remove is NULL) GROUP BY vin) T
                        WHERE FT.fueltypeid = v.fueltypeid
                        AND V.manufacturerID = M.manufacturerID
                        AND VT.vehicletypeID = V.vehicletypeID
                        AND T.vin = V.vin
                        AND PT.vin = V.vin
                        AND NOT EXISTS (SELECT * FROM SalesTransaction ST WHERE ST.vin = V.vin)
                        AND FIND_IN_SET(colorId, colorids)'''

        

        if vehicleType:
            
            query += " AND VT.type = '" + vehicleType + "'"
            flag = True
        
        if modelYear:
            query += " AND V.year = " + modelYear
            flag = True

        if manufacturer:
            query += " AND M.manufacturer_name = '" + manufacturer + "'"
            flag = True

        if fuelType:
            query += " AND FT.fuel_type_name = '" + fuelType + "'"
            flag = True
        
        if colors:
            query += " AND " + colors + " IN (V.colorIDs)"
            flag = True

        if keyword:
            query += ''' AND (UPPER(manufacturer_name) LIKE UPPER('%{0}%') OR 
                        UPPER(model) LIKE UPPER('%{0}%') OR 
                        UPPER(year) LIKE UPPER('%{0}%') OR 
                        UPPER(description) LIKE UPPER('%{0}%'))'''.format(keyword)
        
        if vin:
            query += f"AND V.vin = '{vin}'"

        query += " GROUP BY vin, purchase_price ORDER BY vin ASC"

        # print(query)

        cursor = mysql.connection.cursor()
        cursor.execute(query)

        result = cursor.fetchall()
        results = []
        for row in result:
            temp_dict = dict()
            temp_dict['manufacturer'] = row[0]
            temp_dict['vin'] = row[1]
            temp_dict['model'] = row[2]
            temp_dict['modelYear'] = row[3]
            temp_dict['fueltype'] = row[4]
            temp_dict['color'] = str(row[5])
            temp_dict['mileage'] = row[6]
            temp_dict['salesprice'] = row[7]
            results.append(temp_dict)
        
        cursor.close()
        return results

    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT COUNT(V.vin) FROM vehicle V 
                            LEFT JOIN (SELECT distinct vin, statusID FROM partorder WHERE statusID != "installed") T ON V.vin = T.vin
                            LEFT JOIN salestransaction ST ON ST.vin = V.vin
                            WHERE sale_date IS NULL AND statusID IS NULL;''')
    # cursor.execute('''SELECT COUNT(DISTINCT(vin))
    #             FROM vehicle V
    #             WHERE vin NOT IN (SELECT distinct(vin)
    #                         FROM partorder PT
    #                         WHERE statusID != 'installed')
    #                 AND vin NOT IN (SELECT vin 
    #                         FROM salestransaction); ''')

    result = cursor.fetchall()
    total_cars_sale = result[0][0]

    cursor.execute('''SELECT COUNT(distinct vin)FROM partorder WHERE statusID != "installed";  ''')

    result = cursor.fetchall()
    cursor.close()
    data = {'total_cars' : total_cars_sale, 'total_pending_cars': result[0][0]}

    return render_template('search_vehicle.html', data=data)



@app.route('/sell_vehicle', methods=['GET', 'POST'])
def sell_vehicle():
    # update following tables:
    # sales transaction
    # customerID, username, vin sales date
    if request.method == 'GET':
        search_customerID = request.args.get('search_customerID')
        cur = mysql.connection.cursor()
        q_customer = '''SELECT  
                    C.customerID,
                    IFNULL(I.individual_name, B.business_name) as customer,
                    C.email, C.phone_number,
                    C.street, C.city, C.state, C.zip_code
                FROM customer C
                LEFT JOIN
                    (SELECT CONCAT(first_name, ' ', last_name) as individual_name, 
                            customerID
                            FROM individual )I on I.customerID = C.customerID
                LEFT JOIN 
                    (SELECT business_name, customerID
                    FROM business) B on B.customerID = C.customerID
                WHERE C.customerID = '{0}'; '''.format(search_customerID)
        result = cur.execute(q_customer)
        if result > 0:
            customer_info = cur.fetchall()
            cur.close()
            return render_template('sell_vehicle_1.html', customer_info = customer_info)
        else:
            return render_template('sell_vehicle_1.html')
        
    # where is this coming from?
    # vin = request.args.get('vin')

    if request.method == 'POST':
        customerID = request.form.get('buyerID')
        sale_date = request.form.get('salesDate')
        username = request.form.get('username')
        vin = request.form.get('vin')
        # vehicleSELL = request.form
        # vin = vehicleSELL['vin']
        # sale_date = vehicleSELL['salesDate']
        # username = vehicleSELL['username']
        # customerID = vehicleSELL['buyerID']

        cur = mysql.connection.cursor()
        cur.execute(''' SELECT (MAX(saleID)+1) FROM salestransaction;''')
        saleID = cur.fetchall()
        cur.close()

        # use res here to check if we already have sold this vehicle
        cur = mysql.connection.cursor()
        q = f"SELECT 1 FROM salestransaction WHERE salestransaction.vin = '{vin}'"
        # print(q)
        cur.execute(q)
        res = cur.fetchall()
        cur.close()
        
        if res:
            flash("Vehicle has already been sold. ", "warning")
            return render_template('sell_vehicle_1.html')
            
        #         cur = mysql.connection.cursor()
        # cur.execute('''SELECT customerID from customer;''')
        # ids = cur.fetchall()
        # cur.close()
        # db_ids = [item[0] for item in ids]
        # if customerID in db_ids:
        #     flash('Customer not added: already in database', 'warning')
        #     return  render_template('add_individual.html')

        if not res:
            q = 'INSERT INTO salestransaction(saleID, customerID, username, vin, sale_date) VALUES(%s, %s, %s, %s, %s)'

            cur = mysql.connection.cursor()
            cur.execute(q, (saleID, customerID, username, vin, sale_date))
            mysql.connection.commit()
            cur.close()
        return redirect(url_for('search_vehicle'))
    # return render_template(url_for('sell_vehicle.html'))
    return render_template('sell_vehicle_1.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')
        cursor = mysql.connection.cursor()
        results = cursor.execute('''SELECT role_name FROM user inner join userrole UR on UR.roleID = user.roleID WHERE username = '{0}' and password = '{1}' '''.format(name, password))
        # print('''SELECT role_name FROM USER inner join userrole UR on UR.roleID = user.roleID WHERE username = '{0}' and password = '{1}' '''.format(name, password))
        results = cursor.fetchall()
        cursor.close()
        if not results:
            flash('Invalid Credentials. Please try again', 'warning')
        else:
            print('user logged in', results[0][0])
            response = make_response(redirect('/'))
            response.set_cookie('userrole', results[0][0])
            return response

        # cursor.close()

    return render_template('index.html')


@app.route('/vehicle_detail', methods=['GET', 'POST'])
def vehicle_detail():
    
    vin = str(request.args.get('vin'))
    cursor = mysql.connection.cursor()
    results = cursor.execute('''SELECT V.vin, VT.type, manufacturer_name, year, FT.fuel_type_name, mileage, 
                                    ROUND(((PT.purchase_price * 1.25) + (COALESCE(T.part_price, 0) * 1.1)), 2) as price, 
                                    PT.purchase_price,
                                    ROUND(T.part_price,2), 
                                    V.colorIDs, 
                                    PT.purchase_date, 
                                    U.first_name, U.last_name FROM vehicle V
                                    INNER JOIN vehicleType VT ON VT.vehicletypeID = V.vehicletypeID
                                    INNER JOIN manufacturer M on M.manufacturerID = V.manufacturerID
                                    INNER JOIN fueltype FT on FT.fueltypeID = V.fueltypeID
                                    INNER JOIN purchasetransaction PT on PT.vin = V.vin
                                    INNER JOIN user U on U.username = PT.username
                                    LEFT JOIN (
                                    SELECT vin, SUM(quantity * price) as part_price FROM partorder
                                    GROUP BY vin) T ON T.vin = V.vin
                                WHERE V.vin = '{0}'
                                ORDER BY V.vin ASC; 
                                '''.format(vin))
    
    result = cursor.fetchall()


    data = dict()
    data['vin'] = result[0][0]
    data['vehicleType'] = result[0][1]
    data['manufacturer'] = result[0][2]
    data['modelYear'] = result[0][3]
    data['fuelType'] = result[0][4]
    data['mileage'] = result[0][5]
    data['salesPrice'] = result[0][6]
    data['originalPrice'] = result[0][7]
    data['totalPartPrice'] = result[0][8]
    data['colors'] = result[0][9]
    data['purchase_date'] = result[0][10]
    data['clerk_name'] = result[0][11] + " " + result[0][12]

    # print('''SELECT group_concat(color_name) FROM color WHERE colorID in {0}'''.format(data['colors']))
    results = cursor.execute('''SELECT group_concat(color_name) FROM color WHERE colorID in ({0})'''.format(data['colors']))

    result = cursor.fetchall()

    data['colors'] = result[0][0]

    results = cursor.execute(''' SELECT part_number, vendor_name, quantity, description, price, (price * quantity) as total, 
                                    statusID, CONCAT(vin,'-' , order_num) as orderID FROM partorder
                                    WHERE vin ='{0}' '''.format(vin))
    result = cursor.fetchall()


    data['parts'] = []

    for part in result:
        temp = dict()
        temp['partNumber'] = part[0]
        temp['vendor'] = part[1]
        temp['quantity'] = part[2]
        temp['description'] = part[3]
        temp['cost'] = part[4]
        temp['total'] = part[5]
        temp['status'] = part[6]
        temp['purchaseOrder'] = part[7]

        data['parts'].append(temp)

    cursor.close()

    cursor = mysql.connection.cursor()
    results = cursor.execute(
        '''
    select vehicle.vin 
    from vehicle
    where vin in (
        select vin from salestransaction
    )
    or vin in (
        select vin from partorder
        where statusID = 'ordered' or statusID = 'recieved');
        '''
    )
    result = cursor.fetchall()
    # print(result)
    owner_cant_sell_these = [item[0] for item in result]
    # print(owner_cant_sell_these)
    # print(len(owner_cant_sell_these))
    data['owner_sell_button'] = True
    if vin in owner_cant_sell_these:
        data['owner_sell_button'] = False
    # print(vin)
    # print(owner_cant_sell_these)
    # print(data['owner_sell_button'])

    cursor.close()

    return render_template('vehicle_detail.html', data=data)

@app.route('/parts_order_form', methods=['GET', 'POST'])
def parts_order_form():
    if request.method == 'POST':
        vin = request.args.get('vin')
        vendor_name = request.form.get('vendorName')
        part_number = request.form.getlist('partNumber')
        description = request.form.getlist('description')
        quantity = request.form.getlist('quantity')
        cost = request.form.getlist('cost')
        status = request.form.getlist('status')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT MAX(order_num) FROM partorder WHERE vin = '{0}' ".format(vin) )
        result = cursor.fetchall()
        order_num = ""

        if result[0][0]:
            order_num = str(int(result[0][0]) + 1).zfill(len(result[0][0]))
        else:
            order_num = "001"

        query = ''' INSERT INTO partorder(vin, vendor_name, order_num, part_number, description, price, statusID, quantity) VALUES'''

        for i in range(len(part_number)):
            # print(vin, vendor_name, order_num, part_number[i], description[i], quantity[i], cost[i], status[i])
            part_number_1 = str(part_number[i])
            # print(part_number_1)
            query += '''('{0}', '{1}', '{2}', '{3}', '{4}', {5}, '{6}', {7}), '''.format(vin, vendor_name, order_num, part_number[i], description[i], cost[i], status[i], quantity[i])

        query = query[:-2]

        cursor.execute(query)
        mysql.connection.commit()
        
        cursor.close()
        return redirect(request.url)

    return render_template('parts_order_form.html')

@app.route('/search_vendor', methods=[ 'POST'])
def search_vendor():
    if request.method == 'POST':
        vendor_name = request.args.get('vendorName')
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT vendor_name from vendor WHERE vendor_name = '{0}';'''.format(vendor_name))

        result = cursor.fetchall()
        if result:
            return {"vendorFound": True, "vendorName": result[0][0]}

        cursor.close()
    return {}


@app.route('/submit_vendor', methods=['POST'])
def submit_vendor():
    if request.method == 'POST':
        vendor_name = request.form.get('vendorName')
        phone_number = request.form.get('phoneNumber')
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        zipCode = request.form.get('zipCode')

        cursor = mysql.connection.cursor()
        cursor.execute(''' INSERT INTO vendor(vendor_name, phone, street, city, state, zip_code)
                            VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')'''.format(vendor_name, phone_number,
                                                                                        street, city, state, zipCode))

        mysql.connection.commit()
        cursor.close()
        return {}


@app.route('/seller_information', methods=['POST'])
def seller_information():
    if request.method == 'POST':
        vin = request.args.get('vin')

        cursor = mysql.connection.cursor()
        cursor.execute(''' SELECT first_name, last_name, email, phone_number, street, city, state, zip_code from customer 
                                        inner join 
                                        (select customerID, first_name, last_name from individual
                                        UNION
                                        select customerID, first_name, last_name from Business) T on T.customerId = customer.customerid
                                        inner join purchasetransaction PT ON PT.customerId = customer.customerid WHERE PT.vin = '{0}' '''.format(
            vin))

        # buyer info
        # cursor.execute(''' SELECT first_name, last_name, email, phone_number, street, city, state, zip_code from customer
        #                         inner join
        #                         (select customerID, first_name, last_name from individual
        #                         UNION
        #                         select customerID, first_name, last_name from business) T on T.customerID = customer.customerID
        #                         inner join salestransaction ST ON ST.customerID = customer.customerID WHERE ST.vin = '{0}' '''.format(vin))

        result = cursor.fetchall()

        cursor.close()

        data = dict()

        if result:

            data['name'] = result[0][0] + " " + result[0][1]
            data['email'] = result[0][2]
            data['phone_number'] = result[0][3]
            data['street'] = result[0][4]
            data['city'] = result[0][5]
            data['state'] = result[0][6]
            data['zipcode'] = result[0][7]

        return data

@app.route('/buyer_information', methods=['POST'])
def buyer_information():
    if request.method == 'POST':
        vin = request.args.get('vin')

        cursor= mysql.connection.cursor()
        cursor.execute(''' SELECT first_name, last_name, email, phone_number, street, city, state, zip_code from customer 
                                inner join 
                                (select customerID, first_name, last_name from individual
                                UNION
                                select customerID, first_name, last_name from business) T on T.customerID = customer.customerID
                                inner join salestransaction ST ON ST.customerID = customer.customerID WHERE ST.vin = '{0}' '''.format(vin))

        # seller info
        # cursor.execute(''' SELECT first_name, last_name, email, phone_number, street, city, state, zip_code from customer
        #                         inner join
        #                         (select customerID, first_name, last_name from individual
        #                         UNION
        #                         select customerID, first_name, last_name from Business) T on T.customerId = customer.customerid
        #                         inner join purchasetransaction PT ON PT.customerId = customer.customerid WHERE PT.vin = '{0}' '''.format(vin))

        result = cursor.fetchall()

        data = dict()
        if (result):
            data['name'] = result[0][0] + " " + result[0][1]
            data['email'] = result[0][2]
            data['phone_number'] = result[0][3]
            data['street'] = result[0][4]
            data['city'] = result[0][5]
            data['state'] = result[0][6]
            data['zipcode'] = result[0][7]
        else:
            data['message'] = 'N/A'

        cursor.close()
        
        # print(data)

        return data

@app.route('/update_part_status', methods=['POST'])
def update_part_status():
    if request.method == 'POST':
        partNumber = request.args.get('partNumber')
        vin, orderNumber = request.args.get('purchaseOrder').split('-')
        newStatus = request.args.get('newStatus')

        cursor = mysql.connection.cursor()
        cursor.execute(f"UPDATE partorder SET statusID = '{newStatus}' WHERE part_number = '{partNumber}' AND vin = '{vin}' AND order_num = '{orderNumber}' ")

        cursor.commit()
        cursor.close()
        
        return {}


    
if __name__ == '__main__':
    app.run(debug=True) 
    