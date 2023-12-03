from flask import Blueprint
from .meta import *
import flask

# Create the 'seller' blueprint
seller = Blueprint('seller', __name__,static_folder="static",template_folder="templates")

# Define routes or other functionalities specific to the 'seller' blueprint
# For example:
"""
@seller.route('/seller')
def seller_home():
    if flask.session['is_seller']:
       return flask.render_template("seller.html")
    else:
        flask.flash("You need to be logged  as a seller")
        return flask.redirect(flask.url_for("login"))

        @seller.route('/seller/create')
def seller_products():
    return 'Here are the products listed by the seller

# You can define more routes and functionalities related to the seller in this file



"""

