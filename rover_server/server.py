import sys
import argparse

from twisted.python import log
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor


class ProtocolConnections(object):
    """
    client request structure:
    <command>:<request-body>

    available client commands:
    DC - device is connecting
    CC - controller is connecting
        on success server in response sends DL
    CD - controller selects device to connect
        on success server in response sends CD:OK
    RE - controller sends communicate to connected device
        request format:
        RE:<REQUEST>

    server request structure:
    <command>:<request-body>
    available server commands to clients:
    RE - server sends communicate sent from connected endpoint

    DL - devices list available for connetion
    SE - client request error

    errors:
    E_10 - invalid client command
    E_20 - no endpoint connected

    """

    devices = set()
    controllers = set()
    protocols = {}

    @classmethod
    def line_received(clk, protocol, line):

        command = clk.get_command(line)
        body = clk.get_body(line)

        # the device is connecting
        if command == 'DC':
            clk.connect_device(protocol, body)

        # the contorller is connecting
        elif command == 'CC':
            clk.connect_controller(protocol, body)

        # controller is connecting to selected device
        elif command == 'CD':
            device_name = body
            device_protocol = clk.protocols[device_name]
            clk.make_connection(device_protocol, protocol)

            protocol.sendLine('CD:OK')

        elif command == 'RE':
            device_protocol = clk.protocols.get(protocol.get_endpoint(), None)
            if device_protocol:
                device_protocol.sendLine('RE:' + body)
            else:
                protocol.sendLine('SE:E_20')

        #invalid client request
        else:
            protocol.sendLine('SE:E_10')

    @classmethod
    def get_command(clk, line):
        return line[:2]

    @classmethod
    def get_body(clk, line):
        return line[3:]

    @classmethod
    def connect_device(clk, device_protocol, device_name):
        device_protocol.name = device_name
        clk.devices.add(device_name)
        clk.protocols[device_name] = device_protocol
        log.msg("device {} is connected", device_name)

        #notify all controllers about new device
        clk.notify_all_about_available_devices()

    @classmethod
    def notify_all_about_available_devices(clk):
        #notify all controllers about new device
        if clk.controllers:
            devices_available = clk.get_available_devices()
            for controller_name in clk.controllers:
                clk.notify_about_available_devices(
                    clk.protocols[controller_name],
                    devices_available
                )

    @classmethod
    def notify_about_available_devices(clk, protocol, devices_available):
        response_line = 'DL:' + ':'.join(devices_available)
        protocol.sendLine(response_line)

        log.msg(
            'notifying {} about available devices: {}'.format(
                response_line,
                protocol.name,
            )
        )

    @classmethod
    def get_available_devices(clk):
        available_devices = []
        for device_name in clk.devices:
            dev_protocol = clk.protocols[device_name]
            if dev_protocol.get_endpoint() is None:
                available_devices.append(device_name)

        return available_devices

    @classmethod
    def connect_controller(clk, controller_protocol, controller_name):
        controller_protocol.name = controller_name
        clk.controllers.add(controller_name)
        clk.protocols[controller_name] = controller_protocol
        log.msg("controller {} is connected", controller_name)

        #notify connected controller about connected devices
        devices_available = clk.get_available_devices()
        clk.notify_about_available_devices(
            controller_protocol, devices_available
        )

    @classmethod
    def make_connection(clk, device_protocol, controller_protocol):
        device_protocol.connect_endpoint(controller_protocol.name)
        controller_protocol.connect_endpoint(device_protocol.name)
        log.msg("controller {} is connected to device {}".\
            format(
                controller_protocol.name,
                device_protocol.name
            )
        )

        clk.notify_all_about_available_devices()

    @classmethod
    def disconnect_protocol(clk, protocol):
        log.msg('disconnecting protocol {}'.format(protocol.name))

        if protocol.name in clk.devices:
            end_protocol = clk.protocols.get(protocol.get_endpoint(), None)
            if end_protocol is not None:
                end_protocol.disconnect_endpoint()
                end_protocol.sendLine('DD:')

            clk.devices.remove(protocol.name)
            clk.notify_all_about_available_devices()

        elif protocol.name in clk.controllers:
            clk.controllers.remove(protocol.name)
            end_protocol = clk.protocols.get(protocol.get_endpoint(), None)
            if end_protocol is not None:
                end_protocol.disconnect_endpoint()
                clk.notify_all_about_available_devices()

        else:
            log.err('ERROR - protocol {} neither in controllers nor devices'.\
                    format(protocol.name)
            )

        if clk.protocols.pop(protocol.name, None) is None:
            log.err('ERROR - protocol {} not in protocols'.\
                    format(protocol.name)
            )

        protocol.disconnect_endpoint()

    @classmethod
    def reset(clk):

        for p in clk.protocols:
            clk.protocols[p].reset()

        clk.devices = set()
        clk.controllers = set()
        clk.protocols = {}


class ServerProtocol(LineReceiver):

    name = None
    endpoint = None

    def connectionMade(self):
        log.msg("connection from a client made")

    def connectionLost(self, reason):
        log.msg("connection lost: {}".format(reason))

        #disconect from endpoint
        ProtocolConnections.disconnect_protocol(self)

    def lineReceived(self, line):
        log.msg("line received: {}".format(line))

        ProtocolConnections.line_received(self, line)

    def reset(self):
        self.name = None
        self.disconnect_endpoint()

    def connect_endpoint(self, protocol):
        self.endpoint = protocol

    def disconnect_endpoint(self):
        self.endpoint = None

    def get_endpoint(self):
        return self.endpoint


class ServerFactory(Factory):

    def buildProtocol(self, addr):
        return ServerProtocol()


def main():
    DEFAULT_PORT = 8123

    log.startLogging(sys.stdout)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--port",
        help="port on which server will listen for connections",
        action="store_true"
    )

    args = parser.parse_args()

    port = DEFAULT_PORT
    if args.port:
        port = args.port

    reactor.listenTCP(port, ServerFactory())
    reactor.run()


if __name__ == '__main__':
    main()
