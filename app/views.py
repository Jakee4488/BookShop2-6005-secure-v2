from .meta import *
from markupsafe import escape
import datetime


limiter = Limiter(app,default_limits=["200 per day", "50 per hour"])

# can be implemted any of the page
@app.route('/limited')
@limiter.limit("50 per minute") 
def limited_route():
    return jsonify(message="This route is rate-limited.")

@app.errorhandler(429)
def ratelimit_error(e):
    return jsonify(error="ratelimit exceeded", message=str(e.description)), 429



@app.route("/")
def index():
    """
    Main Page.
    """

    #Get data from the DB using meta function
    
    rows = query_db("SELECT * FROM product")
    app.logger.info(rows)
    
    return flask.render_template("index.html",
                                 bookList = rows)
    

@app.route("/search", methods=["GET", "POST"])
def products_search():
    search_query = flask.request.args.get("search")

    if search_query:
        # Query for products that match the search term using LIKE for partial matches
        itemQry = query_db("SELECT * FROM product WHERE name LIKE ?", ['%' + search_query + '%'], one=True)

        if itemQry:
            itemid = itemQry['id']
            theSQL = """
            SELECT * 
            FROM review
            INNER JOIN user ON review.userID = user.id
            WHERE review.productID = ?;
            """
            reviewQry = query_db(theSQL,(itemid,))

            # If there is form interaction and they put something in the basket
            if flask.request.method == "POST":
                quantity = flask.request.form.get("quantity")
                try:
                    quantity = int(quantity)
                except ValueError:
                    flask.flash("Error with quantity input")
                    return flask.render_template("product.html", item=itemQry, reviews=reviewQry)

                app.logger.warning("Buy Clicked %s items", quantity)

                # Add the item and quantity to the session basket
                basket = flask.session.get("basket", {})
                basket[str(itemid)] = quantity
                flask.session["basket"] = basket
                flask.flash("Item Added to Cart")

            # Render the template with the search results
            return flask.render_template("product.html", item=itemQry, reviews=reviewQry)
        else:
            # No product found
            flask.flash("No products found.")
            return flask.redirect(flask.url_for('products'))
    else:
        # No search term provided
        flask.flash("Please enter a product to search.")
        return flask.redirect(flask.url_for('products'))


        
@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if 'admin' not in flask.session:
        flask.flash('Please log in as an admin.')
        return flask.redirect(flask.url_for('login'))
    flask.session['is_admin'] =True
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')  # Corrected database file path
    cursor = conn.cursor()

    # Get a list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(tables)  # Print the table names to check if they are fetched correctly

    table_data = []
# Iterate over the tables and retrieve column information and data for each
    for table in tables:
        table_name = table[0]

        # Get column information for the current table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # Get data from the current table
        cursor.execute(f"SELECT * FROM {table_name}")
        table_data_rows = cursor.fetchall()

        # Create a list of dictionaries containing column names and data for each row
        data = []
        for row in table_data_rows:
            data.append({columns[i][1]: row[i] for i in range(len(columns))})

        table_data.append({
            'table_name': table_name,
            'columns': [column[1] for column in columns],  # Extract column names
            'data': data,  # Add data for the current table
        })

    # Close the database connection
    conn.close()

    return flask.render_template("admin.html", table_data=table_data)
    
    
    
@app.route("/seller", methods=["GET", "POST"])
def seller_dashboard():
   if flask.session['is_seller']:
       return flask.render_template("seller.html")
   else:
        flask.flash("You need to be logged  as a seller")
        return flask.redirect(flask.url_for("login"))
       

    
#seller creation    
@app.route("/seller/create",methods=["GET","POST"])
def create_seller():
    is_seller=False
    if flask.request.method == "POST":
        
        #Get data
        user = flask.request.form.get("email")
        password = flask.request.form.get("password")
        app.logger.info("Attempt to login as %s:%s", user, password)

        theQry = "Select * FROM User WHERE email = ?"

        userQry =  query_db(theQry,(user,), one=True)

        if userQry is None:
            flask.flash("No Such User")
            
        theQry2 = "Select * FROM seller WHERE email = ?"
        userQry2 =  query_db(theQry2,(user,), one=True)
            
        if userQry2 :
            hassed_db_password= userQry["password"]
            if check_password(password,hassed_db_password):
                flask.flash("seller is already registered")
                
                app.logger.info("Login as %s Success", userQry["email"])
                flask.session["user"] = userQry["id"]
                flask.session['email'] =userQry["email"]
                flask.session['is_seller'] =True
                flask.flash("Login Successful")
            
                return flask.redirect(flask.url_for("seller_dashboard"))
            else:
                flask.flash("Password is Incorrect")
                
        else:
            app.logger.info("User is Ok")
            hassed_db_password= userQry["password"]
            
            if check_password(password,hassed_db_password):
                app.logger.info("Login as %s Success", userQry["email"])
                flask.session["user"] = userQry["id"]
                flask.session['email'] =userQry["email"]
                
                flask.flash("Login Successful")
                # Create the user
                app.logger.info("Create New seller")
                theQry = "INSERT INTO seller (id, email, password) VALUES (NULL, ?, ?)"
                userQry = write_db(theQry,(flask.session['email'],password))
                flask.session['is_seller'] =True
                

                flask.flash("Account Created, you can now Login")
                #return (flask.redirect(flask.url_for("seller.html")))
                return flask.render_template("seller.html")
            else:
                flask.flash("Password is Incorrect")
            
    
    return flask.render_template("create_seller.html")
    
    
    
#seller creation    



@app.route("/products", methods=["GET","POST"])
def products():
    """
    Single Page (ish) Application for Products
    """
    theItem = flask.request.args.get("item")
    if theItem:
        
        #We Do A Query for It
        itemQry = query_db("SELECT * FROM product WHERE id = ?",[theItem], one=True)

        #And Associated Reviews
     
        theSQL = """
        SELECT * 
        FROM review
        INNER JOIN user ON review.userID = user.id
        WHERE review.productID = ?;
        """
        reviewQry = query_db(theSQL,[itemQry['id']])
        
        #If there is form interaction and they put somehing in the basket
        if flask.request.method == "POST":

            quantity = flask.request.form.get("quantity")
            try:
                quantity = int(quantity)
            except ValueError:
                flask.flash("Error Buying Item")
                return flask.render_template("product.html",
                                             item = itemQry,
                                             reviews=reviewQry)
            
            app.logger.warning("Buy Clicked %s items", quantity)
            
            #And we add something to the Session for the user to keep track
            basket = flask.session.get("basket", {})

            basket[theItem] = quantity
            flask.session["basket"] = basket
            flask.flash("Item Added to Cart")

            
        return flask.render_template("product.html",
                                     item = itemQry,
                                     reviews=reviewQry)
    else:
        
        books = query_db("SELECT * FROM product")        
        return flask.render_template("products.html",
                                     books = books)


# ------------------
# USER Level Stuff
# ---------------------

@app.route("/verify",methods=['GET','POST'])
def verify():
    user=flask.session["email"]
    if flask.request.method == "POST":
        if flask.session["admin"] and flask.session["email"]:
            otp=flask.request.form.get("otp")
            otp2=flask.session.get("otp")
            if otp2 and otp2 == otp:
                app.logger.info("Login as %s Success",user)
                user_id=flask.session["user_id"]
                flask.session["user"] = user_id
                flask.flash("Admin Login Successful")
                return flask.redirect(flask.url_for("admin_dashboard"))
            else:
                flask.flash("Incorrect Otp")
                return flask.render_template("verify.html")
        elif flask.session["is_seller"] and flask.session["email"]:
            otp=flask.request.form.get("otp")
            otp2=flask.session.get("otp")
            if otp2 and otp2 == otp:
                app.logger.info("Login as %s Success",user)
                user_id=flask.session["user_id"]
                flask.session["user"] = user_id
                flask.flash("Login Successful")
                return flask.redirect(flask.url_for("seller_dashboard"))
            else:
                flask.flash("Incorrect Otp")
                return flask.render_template("verify.html")
        else:
            otp=flask.request.form.get("otp")
            otp2=flask.session.get("otp")
            if otp2 and otp2 == otp:
                app.logger.info("Login as %s Success",user)
                user_id=flask.session["user_id"]
                flask.session["user"] = user_id
                flask.flash("Login Successful")
                return flask.redirect(flask.url_for("index"))
            else:
                flask.flash("Incorrect Otp")
                return flask.render_template("verify.html")
            
    else:
        otp2=send_otp_email(user)
        flask.session["otp"] = otp2
        flask.flash("otp is send to your mail")
        print(otp2)
        return flask.render_template("verify.html")  


@app.route("/user/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        # Get data
        user = flask.request.form.get("email")
        password = flask.request.form.get("password")
        
        app.logger.info("Attempt to login as %s:%s", user, password)

        theQry = "Select * FROM User WHERE email = ?"
        userQry = query_db(theQry, (user,), one=True)

        if userQry is None:
            flask.flash("No Such User")
            return flask.render_template("login.html")

        hashed_db_password = userQry["password"]
        if not check_password(password, hashed_db_password):
            flask.flash("Password is Incorrect")
            return flask.render_template("login.html")

        theQry2 = "Select * FROM admin WHERE email = ?"
        userQry2 = query_db(theQry2, [user,], one=True)

        theQry3 = "Select * FROM seller WHERE email = ?"
        userQry3 = query_db(theQry3, [user,], one=True)
        
        flask.session["email"] = user
        flask.session["user_id"] = userQry["id"]

        if userQry2:
            app.logger.info("admin is Ok")
            flask.session["admin"] = True
            flask.session["is_seller"] = True
            return flask.redirect(flask.url_for("verify"))
        elif userQry3:
            app.logger.info("seller is Ok")
            flask.session["is_seller"] = True
            flask.session["admin"] = False
            return flask.redirect(flask.url_for("verify"))
        else:
            app.logger.info("User is Ok")
            flask.session["is_seller"] = False
            flask.session["admin"] = False
            return flask.redirect(flask.url_for("verify"))
            
    return flask.render_template("login.html")

    


@app.route("/user/terms.html")
def terms():
    return flask.render_template("terms.html")
    
    


@app.route("/user/create", methods=["GET","POST"])

def create():
    """ Create a new account,
    we will redirect to a homepage here
    """

    if flask.request.method == "GET":
        return flask.render_template("create_account.html")
    
    # Get the form data
    email = flask.request.form.get("email")
    password = flask.request.form.get("password")
    password2 = flask.request.form.get("password2")
    term_check = flask.request.form.get("term_check")
    password_condition, error_code = is_valid_password(password) 

    # Sanity check: Ensure all required fields are filled
    if not email or not password or not password2:
        flask.flash("Not all info supplied")
        return flask.render_template("create_account.html")  # Return the template here
    
    # Use 'elif' for the following checks
    elif email or password or password2:
        # Check if the password doesn't match
        if password != password2:
            flask.flash("Password doesn't match ")
            return flask.render_template("create_account.html")  # Return the template here
        
        # Check if the password is valid
        elif not password_condition:
            flask.flash(f"{error_code}")
            flask.flash("Password does not meet the criteria!!!!!!")
            return flask.render_template("create_account.html")  # Return the template here
        
        # Check if terms and conditions are accepted
        elif not term_check:
            flask.flash("Please accept terms and conditions")
            return flask.render_template("create_account.html")  # Return the template here
        
        else:
            theQry = "SELECT * FROM User WHERE email = ?"
            userQry = query_db(theQry, (email,),one=True)

            if userQry:
                flask.flash("A User with that Email Exists")
                return flask.render_template("create_account.html")  # Return the template here
    
            else:
                hashed_password = hash_password(password)
                # Create the user
                app.logger.info("Create New User")
                theQry = "INSERT INTO user (id, email, password) VALUES (NULL, ?, ?)"

                userQry = write_db(theQry,(email,hashed_password))

                flask.flash("Account Created, you can now Login")
                return flask.redirect(flask.url_for("login"))
        
            
            
        
    #Otherwise we can add the user
    

@app.route("/user/<userId>/settings")
def settings(userId):
    """
    Update a users settings, 
    Allow them to make reviews
    """

    theQry = "Select * FROM User WHERE id = ?"                                                   
    thisUser =  query_db(theQry, (userId,),one=True)

    
    if not thisUser:
        flask.flash("No Such User")
        return flask.redirect(flask.url_for("index"))

    #Purchases
    theSQL = "Select * FROM purchase WHERE userID = ?"
    purchaces = query_db(theSQL,(userId,))

    theSQL = """
    SELECT productId, date, product.name
    FROM purchase
    INNER JOIN product ON purchase.productID = product.id
    WHERE userID = ?;
    """

    purchaces = query_db(theSQL,(userId,))
    
    return flask.render_template("usersettings.html",
                                 user = thisUser,
                                 purchaces = purchaces)

    
@app.route("/logout")
def logout():
    """
    Login Page
    """
    flask.session.clear()
    return flask.redirect(flask.url_for("index"))
    


@app.route("/user/<userId>/update", methods=["GET","POST"])
def updateUser(userId):
    """
    Process any chances from the user settings page
    """

    theQry = "Select * FROM User WHERE id = ?"   
    thisUser = query_db(theQry,(userId,), one=True)
    if not thisUser:
        flask.flash("No Such User")
        return flask.redirect(flask.url_for("index"))

    #otherwise we want to do the checks
    if flask.request.method == "POST":
        current = flask.request.form.get("current")
        password = flask.request.form.get("password")
        app.logger.info("Attempt password update for %s from %s to %s", userId, current, password)
        app.logger.info("%s == %s", current, thisUser["password"])
        if current:
            if current == thisUser["password"]:
                app.logger.info("Password OK, update")
                #Update the Password
                theSQL = "UPDATE user SET password = ? WHERE id = ? "
                app.logger.info("SQL %s", theSQL)
                write_db(theSQL,[password,userId])
                flask.flash("Password Updated")
                
            else:
                app.logger.info("Mismatch")
                flask.flash("Current Password is incorrect")
            return flask.redirect(flask.url_for("settings",
                                                userId = thisUser['id']))

            
    
        flask.flash("Update Error")

    return flask.redirect(flask.url_for("settings", userId=userId))

# -------------------------------------
#
# Functionality to allow user to review items
#
# ------------------------------------------
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return flask.send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/review/<userId>/<itemId>", methods=["GET", "POST"])
def reviewItem(userId, itemId):
   

    if request.method == "POST":
        reviewStars =  escape(flask.request.form.get("rating"))
        reviewComment =escape (flask.request.form.get("review"))
        reviewId = request.form.get("reviewId")
        file = request.files.get('review_image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename) # Correctly getting just the filename
            file_path = os.path.join(filename) # Path to save the file
            file.save(file_path) # Saving the file
            

    #Handle input
    if flask.request.method == "POST":
        reviewStars =  escape(flask.request.form.get("rating"))
        reviewComment = escape (flask.request.form.get("review"))

        #Clean up review whitespace
        reviewComment = reviewComment.strip()
        reviewId = flask.request.form.get("reviewId")

        app.logger.info("Review Made %s", reviewId)
        app.logger.info("Rating %s  Text %s", reviewStars, reviewComment)
        

        if reviewId:
            #Update an existing review on the database
            app.logger.info("Update Existing")

            theSQL = """
            UPDATE review
            SET stars = ?,
                review = ?
            WHERE
                id = ? """

            app.logger.debug("%s", theSQL)
            write_db(theSQL,[reviewStars,reviewComment,reviewId])

            flask.flash("Review Updated")
            
        else:
            app.logger.info("New Review")

            theSQL ="""
            INSERT INTO review (userId, productId, stars, review)
            VALUES (?, ?, ?, ?);
            """

            app.logger.info("%s", theSQL)
            write_db(theSQL,[userId,itemId,reviewStars,reviewComment])

            flask.flash("Review Made")

    #Otherwise get the review
    theQry = "SELECT * FROM product WHERE id = ?;"
    item = query_db(theQry,itemId, one=True)
    
    theQry = "SELECT * FROM review WHERE userID = ? AND productID = ?;"
    review = query_db(theQry,(userId, itemId), one=True)
    app.logger.debug("Review Exists %s", review)

    return flask.render_template("reviewItem.html",
                                 item = item,
                                 review = review,
                                 )

# ---------------------------------------
#
# BASKET AND PAYMEN
#
# ------------------------------------------



@app.route("/basket", methods=["GET","POST"])
def basket():

    #Check for user
    if not flask.session["user"]:
        flask.flash("You need to be logged in")
        return flask.redirect(flask.url_for("index"))


    theBasket = []
    #Otherwise we need to work out the Basket
    #Get it from the session
    sessionBasket = flask.session.get("basket", None)
    if not sessionBasket:
        flask.flash("No items in basket")
        return flask.redirect(flask.url_for("index"))

    totalPrice = 0
    for key in sessionBasket:
        theQry = "SELECT * FROM product WHERE id = ?"
        theItem =  query_db(theQry,(key,), one=True)
        quantity = int(sessionBasket[key])
        thePrice = theItem["price"] * quantity
        totalPrice += thePrice
        theBasket.append([theItem, quantity, thePrice])
    
        
    return flask.render_template("basket.html",
                                 basket = theBasket,
                                 total=totalPrice)

@app.route("/basket/payment", methods=["GET", "POST"])
def pay():
    """
    Fake paymeent.

    YOU DO NOT NEED TO IMPLEMENT PAYMENT
    """
    
    if not flask.session["user"]:
        flask.flash("You need to be logged in")
        return flask.redirect(flask.url_for("index"))

    #Get the total cost
    cost = flask.request.form.get("total")


    
    #Fetch USer ID from Sssion
    theQry = "Select * FROM User WHERE id = ?"
    theUser = query_db(theQry,[flask.session["user"]], one=True)

    #Add products to the user
    sessionBasket = flask.session.get("basket", None)

    theDate = datetime.datetime.utcnow()
    for key in sessionBasket:

        #As we should have a trustworthy key in the basket.
        theQry = "INSERT INTO PURCHASE (userID, productID, date) VALUES (?,?,?)"
                                                                                              
        app.logger.debug(theQry)
        write_db(theQry,[theUser['id'],key,theDate])

    #Clear the Session
    flask.session.pop("basket", None)
    
    return flask.render_template("pay.html",
                                 total=cost)
    
    
# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/user/add_products', methods=['GET', 'POST'])
def add_products():
    if 'user' not in session:
        flask.flash('Please log in to add products.')
        return flask.redirect(flask.url_for('login'))

    if request.method == 'POST':
        # Get product details from the form
        name = request.form.get('name')
        description = escape(request.form.get('description'))
        price = request.form.get('price')
        image = request.files.get('image')

        # Validate the form data
        if not name or not description or not price or not image:
            flask.flash('Please fill out all fields.')
        else:
            # Handle the uploaded image (you can save it to a directory)
            if image:
                # Save the image to your desired directory
                image_filename = secure_filename(image.filename)
                #image.save(os.path.join(image_filename))
                #image.save = os.path.join[UPLOAD_FOLDER]
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

                image.save(file_path)

                # Insert the new product into the database
                insert_query = """
                INSERT INTO product (name, description, price, image, seller_id)
                VALUES (?, ?, ?, ?, ?)
                """
                seller_id = session['user']
                write_db(insert_query, [name, description, price, image_filename, seller_id])

                flask.flash('Product added successfully.')
                return flask.redirect(flask.url_for('edit_products'))

    return flask.render_template('add_products.html')

@app.route('/user/edit_products')
def edit_products():
    if 'user' not in session:
        flask.flash('Please log in to edit your products.')
        return flask.redirect(flask.url_for('login'))

    user_id = session['user']

    # Fetch the seller's products from the product table
    products_query = "SELECT * FROM product WHERE seller_id = ?"
    products = query_db(products_query, [user_id])

    return flask.render_template('edit_products.html', products=products)

@app.route('/user/edit_products/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user' not in session:
        flask.flash('Please log in to edit your products.')
        return flask.redirect(flask.url_for('login'))

    user_id = session['user']

    # Fetch the product from the database
    product_query = "SELECT * FROM product WHERE id = ? AND seller_id = ?"
    product = query_db(product_query, [product_id, user_id], one=True)

    if not product:
        flask.flash('Product not found or you do not have permission to edit it.')
        return flask.redirect(flask.url_for('edit_products'))

    if request.method == 'POST':
        # Get updated product details from the form
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')

        # Validate the form data
        if not name or not description or not price:
            flask.flash('Please fill out all fields.')
        else:
            # Update the product information in the database
            update_query = """
            UPDATE product
            SET name = ?, description = ?, price = ?
            WHERE id = ? AND seller_id = ?
            """
            write_db(update_query, [name, description, price, product_id, user_id])

            flask.flash('Product updated successfully.')
            return flask.redirect(flask.url_for('edit_products'))

    return flask.render_template('edit_product.html', product=product)



# ---------------------------
# HELPER FUNCTIONS
# ---------------------------


@app.route('/uploads/<name>')
def serve_image(name):
    """
    Helper function to serve an uploaded image
    """
    return flask.send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route("/initdb")
def database_helper():
    """
    Helper / Debug Function to create the initial database

    You are free to ignore scurity implications of this
    """
    init_db()
    return "Done"

