# -*- coding: utf-8 -*-

"""Console script for xled."""

from __future__ import absolute_import

import locale
import logging
import time

import click
import click_log

import xled.auth
import xled.control
import xled.discover
import xled.exceptions
import xled.security

log = logging.getLogger(__name__)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

log.addHandler(ch)


def common_preamble(name=None, host_address=None):
    if name:
        click.echo("Looking for a device with name: {}...".format(name))
    elif host_address:
        click.echo("Looking for device with address: {}...".format(host_address))
    else:
        click.echo("Looking for any device...")
    hw_address, device_name, ip_address = xled.discover.discover(
        find_name=name, destination_host=host_address
    )
    if name:
        click.echo("Working on requested device.".format(device_name))
    else:
        click.echo("Working on device: {}".format(device_name))
    log.debug("HW address = %s", hw_address)
    log.debug("IP address = %s", ip_address)

    return xled.control.ControlInterface(ip_address, hw_address)


def validate_time(ctx, param, value):
    try:
        struct_time = time.strptime(value, "%H:%M")
        return (struct_time.tm_hour, struct_time.tm_min)
    except ValueError:
        raise click.BadParameter("Time needs to be in format HH:MM.")


@click.group()
@click.version_option()
@click.pass_context
@click.option(
    "--name",
    metavar="DEVICE_NAME",
    help="Name of the device to operate on. Mutually exclusive with --hostname.",
)
@click.option(
    "--hostname",
    metavar="ADDRESS",
    help="Address of the device to operate on. Mutually exclusive with --name.",
)
@click_log.simple_verbosity_option(
    log,
    "--verbosity-cli",
    help="Sets verbosity of main CLI. Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
)
@click_log.simple_verbosity_option(
    xled.discover.log,
    "--verbosity-discover",
    help="Sets verbosity of discover module. Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
)
@click_log.simple_verbosity_option(
    xled.control.log,
    "--verbosity-control",
    help="Sets verbosity of control module. Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
)
@click_log.simple_verbosity_option(
    xled.auth.log,
    "--verbosity-auth",
    help="Sets verbosity of auth module. Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
)
def main(ctx, name, hostname):
    if name and hostname:
        raise click.BadParameter("Either name or hostname can be set not both.")
    ctx.obj = {"name": name, "hostname": hostname}


@main.command(name="get-mode", help="Gets current device mode.")
@click.pass_context
def get_mode(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    mode = control_interface.get_mode()
    click.echo("Device in mode {}.".format(mode["mode"]))


@main.command(name="on", help="Turns device on and starts last used movie.")
@click.pass_context
def turn_on(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Turning on...")
    control_interface.set_mode("movie")
    click.echo("Turned on.")


@main.command(name="off", help="Turns device off.")
@click.pass_context
def turn_off(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Turning off...")
    control_interface.set_mode("off")
    click.echo("Turned off.")


@main.command(name="get-timer", help="Gets current timer settings.")
@click.pass_context
def get_timer(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Getting timer...")
    timer = control_interface.get_timer()

    format = locale.nl_langinfo(locale.T_FMT)
    t = xled.util.date_from_seconds_after_midnight(timer["time_now"]).strftime(format)
    click.echo("Time now: {}.".format(t))
    if timer["time_on"] == -1:
        click.echo("Time to turn on not set.")
    else:
        t = xled.util.date_from_seconds_after_midnight(timer["time_on"]).strftime(
            format
        )
        click.echo("Turn on {}.".format(t))
    if timer["time_off"] == -1:
        click.echo("Time to turn off not set.")
    else:
        t = xled.util.date_from_seconds_after_midnight(timer["time_off"]).strftime(
            format
        )
        click.echo("Turn off {}.".format(t))


@main.command(name="set-timer", help="Sets timer.")
@click.argument("time-on", callback=validate_time)
@click.argument("time-off", callback=validate_time)
@click.pass_context
def set_timer(ctx, time_on, time_off):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    seconds_on = xled.control.seconds_after_midnight_from_time(*time_on)
    seconds_off = xled.control.seconds_after_midnight_from_time(*time_off)
    log.debug("Setting timer...")
    control_interface.set_timer(seconds_on, seconds_off)
    click.echo("Timer set.")


@main.command(name="disable-timer", help="Disables timer.")
@click.pass_context
def disable_timer(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Disabling timer...")
    control_interface.set_timer(-1, -1)
    click.echo("Timer disabled.")


@main.command(name="get-device-name", help="Gets current device name.")
@click.pass_context
def get_device_name(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Getting device name...")
    name = control_interface.get_device_name()
    click.echo("Device name: {}".format(name["name"]))


@main.command(name="set-device-name", help="Sets device name.")
@click.argument("name")
@click.pass_context
def set_device_name(ctx, name):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Setting device name...")
    control_interface.set_device_name(name)
    click.echo("Set new name to {}".format(name))


@main.command(name="upload-movie", help="Uploads movie.")
@click.argument("movie", type=click.File("rb"))
@click.pass_context
def upload_movie(ctx, movie):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Uploading movie...")
    response = control_interface.set_led_movie_full(movie)
    click.echo("Uploaded {} frames.".format(response["frames_number"]))


@main.command(name="update-firmware", help="Updates firmware.")
@click.argument("stage0", type=click.File("rb"))
@click.argument("stage1", type=click.File("rb"))
@click.pass_context
def update_firmware(ctx, stage0, stage1):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))

    fw_stage_sums = [None, None]
    for stage in (0, 1):
        # I don't know how to dynamically construct variable name
        if stage == 0:
            fw_stage_sums[stage] = xled.security.sha1sum(stage0)
        elif stage == 1:
            fw_stage_sums[stage] = xled.security.sha1sum(stage1)
        log.debug("Firmware stage %d SHA1SUM: %r", stage, fw_stage_sums[stage])
        if not fw_stage_sums[stage]:
            click.echo(
                "Failed to compute SHA1SUM for firmware stage %d.".format(stage),
                err=True,
            )
            return 1

    stage0.seek(0)
    stage1.seek(0)
    uploaded_stage_sums = [None, None]
    for stage in (0, 1):
        log.debug("Uploading firmware stage %d...", stage)
        # I still don't know how to dynamically construct variable name
        if stage == 0:
            response = control_interface.firmware_0_update(stage0)
        elif stage == 1:
            response = control_interface.firmware_1_update(stage1)
        log.debug("Firmware stage %d uploaded.", stage)
        if not response.ok:
            click.echo(
                "Failed to upload stage {}: {}".format(stage, response.status_code),
                err=True,
            )
            return 1
        uploaded_stage_sums[stage] = response.get("sha1sum")
        log.debug("Uploaded stage %d SHA1SUM: %r", stage, uploaded_stage_sums[stage])
        if not uploaded_stage_sums[stage]:
            click.echo(
                "Device didn't return SHA1SUM for stage {}.".format(stage), err=True
            )
            return 1

    if fw_stage_sums != uploaded_stage_sums:
        log.error(
            "Firmware SHA1SUMs: %r != uploaded SHA1SUMs",
            fw_stage_sums,
            uploaded_stage_sums,
        )
        click.echo(
            "Firmware SHA1SUMs doesn't match to uploaded SHA1SUMs.".format(stage),
            err=True,
        )
        return 1
    else:
        log.debug("Firmware SHA1SUMs matches.")

    response = control_interface.firmware_update(fw_stage_sums[0], fw_stage_sums[1])
    if not response.ok:
        click.echo(
            "Failed to update firmware: {}.".format(response.status_code), err=True
        )
        return 1
    click.echo("Firmware update successful.")
