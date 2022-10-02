from flask import Flask, session, render_template, url_for
from flask import Flask, redirect, jsonify, json, request

import stripe

app = Flask(__name__)

# This is your test secret API key.
stripe.api_key = 'sk_test_51LnnRESDCt1OREgP0XnfJoDLz6wh5dToklLTGFIaCeLXUfOmwW0SKwJrlHPFobCTFxz9uffCWOZyF4Q98pDfUXo300seR8hQH7'

YOUR_DOMAIN = 'http://localhost:5000'
app.secret_key = 'asdsdfsdfs13sdf_df%&'
subscription_map = {}
user_session_map = {}
register_user = {}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' not in request.form:
        return render_template('login.html')
    if request.form['username'] not in register_user:
        return render_template('signup.html')
    session['username'] = request.form['username']
    return redirect(url_for('index'))


@app.route('/signup-screen', methods=['GET', 'POST'])
def signup_screen():
    return render_template('signup.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    register_user[request.form['username']] = True
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/')
def index():
    login1 = False
    if 'username' in session:
        login1 = True
    else:
        return redirect(url_for('login'))
    if session['username'] in subscription_map:
        valid_sub = True
    else:
        valid_sub = False
    return render_template('user-home.html', login=login1, valid_sub=valid_sub)


@app.route('/create-portal-session', methods=['POST', 'GET'])
def customer_portal():
    login1 = False
    if 'username' in session:
        login1 = True
    else:
        return redirect(url_for('login'))
    # For demonstration purposes, we're using the Checkout session to retrieve the customer ID.
    # Typically this is stored alongside the authenticated user in your database.
    checkout_session_id = user_session_map[session['username']]
    checkout_session = stripe.checkout.Session.retrieve(checkout_session_id)

    # This is the URL to which the customer will be redirected after they are
    # done managing their billing with the portal.
    return_url = YOUR_DOMAIN

    portalSession = stripe.billing_portal.Session.create(
        customer=checkout_session.customer,
        return_url=return_url,
    )
    return redirect(portalSession.url, code=303)


@app.route('/success', methods=['GET'])
def success():
    login1 = False
    if 'username' in session:
        login1 = True
    else:
        return redirect(url_for('login'))
    session_id = request.args.get('session_id')
    user_session_map[session['username']] = session_id
    subscription_map[session['username']] = get_subscription_id(session_id)
    # return render_template('success.html', session_id=session_id)

    return redirect(url_for('customer_portal'))


def get_subscription_id(session_id):
    retrieved_session = stripe.checkout.Session.retrieve(session_id)
    return retrieved_session['subscription']


@app.route('/subscription', methods=['GET'])
def subscription_list():
    login1 = False
    if 'username' in session:
        login1 = True
    else:
        return redirect(url_for('login'))
    result = stripe.Subscription.retrieve(subscription_map[session['username']])

    return render_template("subs.html", status=result['items']['data'][0]['price']['active'], subid=result['id'],
                           priceid=result['items']['data'][0]['price']['id'])


@app.route('/cancel_subscription', methods=['GET'])
def subscription_cancel():
    login1 = False
    if 'username' in session:
        login1 = True
    else:
        return redirect(url_for('login'))
    result = stripe.Subscription.delete(subscription_map[session['username']])
    del subscription_map[session['username']]
    del user_session_map[session['username']]
    return render_template("subs.html", status=result['items']['data'][0]['price']['active'], subid=result['id'],
                           priceid=result['items']['data'][0]['price']['id'])


# @app.route('/webhook', methods=['POST'])
# def webhook_received():
#     # Replace this endpoint secret with your endpoint's unique secret
#     # If you are testing with the CLI, find the secret by running 'stripe listen'
#     # If you are using an endpoint defined with the API or dashboard, look in your webhook settings
#     # at https://dashboard.stripe.com/webhooks
#     webhook_secret = 'whsec_12345'
#     request_data = json.loads(request.data)
#
#     if webhook_secret:
#         # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
#         signature = request.headers.get('stripe-signature')
#         try:
#             event = stripe.Webhook.construct_event(
#                 payload=request.data, sig_header=signature, secret=webhook_secret)
#             data = event['data']
#         except Exception as e:
#             return e
#         # Get the type of webhook event sent - used to check the status of PaymentIntents.
#         event_type = event['type']
#     else:
#         data = request_data['data']
#         event_type = request_data['type']
#     data_object = data['object']
#
#     print('event ' + event_type)
#
#     if event_type == 'checkout.session.completed':
#         print('🔔 Payment succeeded!')
#     elif event_type == 'customer.subscription.trial_will_end':
#         print('Subscription trial will end')
#     elif event_type == 'customer.subscription.created':
#         print('Subscription created %s', event.id)
#     elif event_type == 'customer.subscription.updated':
#         print('Subscription created %s', event.id)
#     elif event_type == 'customer.subscription.deleted':
#         # handle subscription canceled automatically based
#         # upon your subscription settings. Or if the user cancels it.
#         print('Subscription canceled: %s', event.id)
#
#     return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)
