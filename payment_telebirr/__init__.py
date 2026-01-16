from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider

def post_init_hook(env):
    """Function to set up the payment provider 'telebirr' after
    module installation."""
    setup_provider(env, 'telebirr')


def uninstall_hook(env):
    """Function to reset the payment provider 'telebirr' before module
    uninstallation."""
    reset_payment_provider(env, 'telebirr')

