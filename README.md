# clearskies-stripe

clearskies bindings for working with [Stripe](https://stripe.com/).  Mostly this means handlers and actions to control the flow of data to and from stripe.

# Installation

To install:

```
pip install clear-skies-stripe
```

# Usage

## Authentication

This module has a variety of actions and handlers which take care of the stripe integration.  However, before you can use any of them, you must setup the stripe module with clearskies and tell it how to authenticate to Stripe.  The module assumes that your Stripe API key is stored in your secret manager, so you just have to tell it the path to the API key in your secret manager.

**IMPORTANT**: This module is designed to fetch your Stripe API key only when needed and will automatically re-fetch the key from the secrets manager in the event of an authentication failure.  As a result, you can rotate your Stripe API key at anytime: just drop the new API key in your secret manager and your running processes will automatically find it and use it without needing to restart/rebuild/relaunch the application.

In the following example, we configure a clearskies application to use AWS Secrets Manager for the storage of secrets, and then we tell the Stripe integration to fetch its api key from `/path/to/stripe/(api|publishable)/key` in AWS Secrets Manager.  Of course, you can use any secrets manager you want: just swap out `secrets` in the dependency injection configuration.

```
import clearskies
import clearskies_stripe
import clearskies_aws

application = clearskies.Application(
    SomeHandler,
    {
        "your": "application config",
    },
    bindings={
        "stripe": clearskies_stripe.di.stripe(
            "/path/to/stripe/api/key",
            "/path/to/stripe/publishable/key",
        ),
        "secrets": clearskies_aws.secrets.SecretsManager,
    },
)
```

## Models

To use any of the models you must import the `clearskies_stripe` module into your application (you still have to configure authentication per the above):

```
import clearskies
import clearskies_stripe
import clearskies_aws

application = clearskies.Application(
    SomeHandler,
    {
        "your": "application config",
    },
    binding_modules=[
        clearskies_stripe,
    ],
    bindings={
        "stripe": clearskies_stripe.di.stripe(
            "/path/to/stripe/api/key",
            "/path/to/stripe/publishable/key",
        ),
        "secrets": clearskies_aws.secrets.SecretsManager,
    },
)
```

## Models

This module comes with a limited selection of models.  The columns available in each model match those published via the Stripe API.

| Model               | DI name               | Stripe Docs |
|---------------------|-----------------------|-------------|
| StripeCustomer      | stripe_customer       | TBD |
| StripePayment       | stripe_payment        | TBD |
| StripePaymentMethod | stripe_payment_method | TBD |

## SetupIntent Handler

This handler creates a SetupIntent and returns the details of it, as well as the publishable key.  You can specify any of the parameters for the [create call].  In addition, you can provide `parameters_callable` which can change all the parameters that will be passed to the create call, and you can also provide `output_callable` which changes the response from the handler.  By default, the handler returns the full details of the response from the create call, as well as your publishable key.

### Configuration Options

Here are the list of allowed configurations for this handler (on top of the standard handler configs).  All configs are optional.  With the exception of the callables (described below), all configuration options will be passed along as-is in the call to `stripe.setup_intents.create()`.  See [the stripe docs](https://docs.stripe.com/api/setup_intents/create) for more details:

| Name                           | Type        |
|--------------------------------|-------------|
| `automatic_payment_methods`    | `dict`      |
| `confirm`                      | `bool`      |
| `description`                  | `str`       |
| `metadata`                     | `dict`      |
| `payment_method`               | `str`       |
| `usage`                        | `str`       |
| `attach_to_self`               | `bool`      |
| `confirmation_token`           | `str`       |
| `flow_directions`              | `list[str]` |
| `mandate_data`                 | `dict`      |
| `on_behalf_of`                 | `str`       |
| `payment_method_configuration` | `str`       |
| `payment_method_data,`         | `dict`      |
| `payment_method_options`       | `dict`      |
| `payment_method_types`         | `list[str]` |
| `return_url`                   | `str`       |
| `single_use`                   | `dict`      |
| `use_stripe_sdk`               | `bool`      |
| `parameters_callable`          | `Callable`  |
| `output_callable`              | `Callable`  |

### parameters_callable

The `parameters_callable` is provided with the following kwargs
| Name                 | Type                                   | Value |
|----------------------|----------------------------------------|-------|
| `input_output`       | `clearskies.input_outputs.InputOutput` | The input output object for the request |
| `routing_data`       | `dict`                                 | Any named routing parameters |
| `request_data`       | `dict`                                 | The contents of the JSON request body |
| `authorization_data` | `dict`                                 | Any authorization data for logged in users |
| `context_specifics`  | `dict`                                 | Any additional data provided by the context the application is running under |

It should return a dictionary, which will be passed along in the SDK call to `setup_intents.create()`.  If the parameters callable returns a parameter that is also specified in the handler configuration, the return value from the parameters callable takes preference.

### output_callable

The `output_callable` will be provided the response from the `setup_intents.create()` call and can make additional changes.  Note that this function **MUST** return a dictionary.  If `output_callable` is defined then it's response will be returned to the user as-is, which means that only the data returned by the callable will be sennt along to the client.

The `output_callable` is provided with the following kwargs:

| Name                 | Type                                   | Value |
|----------------------|----------------------------------------|-------|
| `response`           | `dict`                                 | The response from the `setup_intents.create()` call |
| `input_output`       | `clearskies.input_outputs.InputOutput` | The input output object for the request |
| `routing_data`       | `dict`                                 | Any named routing parameters |
| `request_data`       | `dict`                                 | The contents of the JSON request body |
| `authorization_data` | `dict`                                 | Any authorization data for logged in users |
| `context_specifics`  | `dict`                                 | Any additional data provided by the context the application is running under |

### Example

Here's an example of using the CreateSetupIntent handler.  This example assumes that the stripe customer id is stored in the JWT in the key `stripe_customer_id`, and so it uses that fact in conjunction with the `parameters_callable` to set the customer id on the setup intent:

```
import clearskies
import clearskies_stripe
import clearskies_aws

def add_stripe_customer(self, authorization_data):
    return {"customer": authorization_data["stripe_customer_id"]}

application = clearskies.Application(
    clearskies.handlers.SimpleRouting,
    {
        "authentication": clearskies.authentication.jwks("https://example.com/.well-known/jwks.json"),
        "routes": [
            {
                "path": "/setup_intent",
                "methods": "POST",
                "handler_class": clearskies_stripe.handlers.CreateSetupIntent,
                "handler_config": {
                    "usage": "off_session",
                    "parameters_callable": add_stripe_customer,
                },
            },
        ],
    },
    bindings={
        "stripe": clearskies_stripe.di.stripe(
            "/path/to/stripe/api/key/in/secrets/manager",
            "/path/to/stripe/publishable/key/in/secrets/manager",
        ),
        "secrets": clearskies_aws.secrets.SecretsManager,
    },
)

in_wsgi = clearskies_aws.contexts.wsgi(application)
def application(env, start_response):
    return in_wsgi(env, start_response)

in_lambda = clearskies_aws.contexts.lambda_elb(application)
def lambda_handler(event, context):
    return in_lambda(env, start_response)
```

You would then execute and expect something like this:

```
$ curl 'https://your-application/setup_intent' -X POST | jq
```
