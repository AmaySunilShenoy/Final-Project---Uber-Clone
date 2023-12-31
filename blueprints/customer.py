from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from flask_login import login_required, current_user
from services.sqlite_functions import add_user, update_user, delete_user
from services.customer_services import get_customer,add_payment_method
from loggers.loggers import performance_logger, action_logger
from database.MongoDB.mongo import client
import time
customer_blueprint = Blueprint('customer', __name__)
db = client['Quickie']
rides = db['rides']

# CRUD operations for customer

# Create
@customer_blueprint.route('/register', methods=['POST'])
def register():
    
    first_name = session.get('signup_firstname')
    last_name = session['signup_lastname']
    email = session['signup_email']
    password = session['signup_password']
    card_number = request.form['card_number']
    cvv = request.form['cvv']
    expiry_month = request.form['expiry_month']
    expiry_year = request.form['expiry_year']
    expiration_date = f'{expiry_month}/{expiry_year}'

    try:

        # Creating a user (in SQLite) and adding payment method (in MongoDB)
        user_id = add_user(first_name, last_name, email, password, 'customer')
        add_payment_method(user_id, card_number, cvv, expiration_date)

        # Clearing session variables
        session.pop('signup_firstname')
        session.pop('signup_lastname')
        session.pop('signup_email')
        session.pop('signup_password')
        

        # Logging
        action_logger.info(f'User {user_id} registered as a customer')

        # Flashing and redirecting
        flash('Thank you for registering as a customer', 'success')
        return redirect('/connection')
    except Exception as e:
        flash('An error occurred while registering', 'danger')
        action_logger.error(f'Error in /customer/register: {e}')
        return {'status': 'error'}


# Read
@customer_blueprint.route('/<customer_id>', methods=['GET'])
@login_required
def read(customer_id):
    
    try:
        customer = get_customer(customer_id)
        if customer:
            
            return render_template('customer.html', customer=customer)
        else:
            flash('Customer not found', 'danger')
            return redirect('/home')
    except Exception as e:
        print("Error in /customer/<customer_id>:", e)
        flash('An error occurred while retrieving customer', 'danger')
        action_logger.error(f'Error in /customer/<customer_id>: {e}')
        return redirect('/home')


# Update
@customer_blueprint.route('/update/<customer_id>', methods=['POST'])
@login_required
def update(customer_id):
    update = request.get_json()
    customer = get_customer(customer_id)
    if customer:
        return update_user(customer_id, update)
    else:
        return {'status': 'error', 'error_type': 'Customer not found'}
    

# Delete
@customer_blueprint.route('/delete/<customer_id>', methods=['POST'])
@login_required
def delete(customer_id):
    try:
        result = delete_user(customer_id)
        if result:
            return {'status': 'success'}
        else:
            return {'status': 'error', 'error_type': 'Customer not found'}
    except Exception as e:
        print("Error in /customer/delete/<customer_id>:", e)
        action_logger.error(f'Error in /customer/delete/<customer_id>: {e}')
        return {'status': 'error', 'error_type': 'An error occurred while deleting customer'}