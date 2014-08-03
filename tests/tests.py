from twisted.trial import unittest
from twisted.test import proto_helpers

from rover_server.server import ServerFactory
from rover_server.server import ServerProtocol
from rover_server.server import ProtocolConnections


END_LINE = '\r\n'
DEVICE_NAME = 'mock-client'
CONTROLLER_NAME = 'mock-controller'


class ProtocolConnectionsLineRecievedTest(unittest.TestCase):

    def setUp(self):

        self.tr_device = proto_helpers.StringTransport()
        self.proto_device = ServerProtocol()
        self.proto_device.makeConnection(self.tr_device)

        self.proto_controller = ServerProtocol()
        self.tr_controller = proto_helpers.StringTransport()
        self.proto_controller.makeConnection(self.tr_controller)

    def tearDown(self):
        ProtocolConnections.reset()

    def test_new_device_connecting(self):

        EXPECTED_R_FOR_C = ''
        EXPECTED_R_FOR_D = ''

        REQUEST = 'DC:' + DEVICE_NAME + END_LINE
        self.proto_device.dataReceived(REQUEST)

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, EXPECTED_R_FOR_C)
        self.assertEqual(r_for_device, EXPECTED_R_FOR_D)

        self.assertEqual(len(ProtocolConnections.devices), 1)
        self.assertEqual(len(ProtocolConnections.controllers), 0)
        assert DEVICE_NAME in ProtocolConnections.devices

        self.assertEqual(len(ProtocolConnections.protocols), 1)
        self.assertEqual(ProtocolConnections.protocols[DEVICE_NAME],
                         self.proto_device)

    def test_new_controller_connecting(self):

        EXPECTED_R_FOR_C = 'DL:' + END_LINE
        EXPECTED_R_FOR_D = ''

        REQUEST = 'CC:' + CONTROLLER_NAME + END_LINE
        self.proto_controller.dataReceived(REQUEST)

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, EXPECTED_R_FOR_C)
        self.assertEqual(r_for_device, EXPECTED_R_FOR_D)

        self.assertEqual(len(ProtocolConnections.controllers), 1)
        self.assertEqual(len(ProtocolConnections.devices), 0)
        assert CONTROLLER_NAME in ProtocolConnections.controllers

        self.assertEqual(len(ProtocolConnections.protocols), 1)
        self.assertEqual(ProtocolConnections.protocols[CONTROLLER_NAME],
                         self.proto_controller)

    def test_controller_connects_after_device(self):

        EXPECTED_R_FOR_C = 'DL:' + DEVICE_NAME + END_LINE
        EXPECTED_R_FOR_D = ''

        #device is connecting
        D_REQUEST = 'DC:' + DEVICE_NAME + END_LINE
        self.proto_device.dataReceived(D_REQUEST)

        #controller is connecting
        C_REQUEST = 'CC:' + CONTROLLER_NAME + END_LINE
        self.proto_controller.dataReceived(C_REQUEST)

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, EXPECTED_R_FOR_C)
        self.assertEqual(r_for_device, EXPECTED_R_FOR_D)

        self.assertEqual(len(ProtocolConnections.controllers), 1)
        self.assertEqual(len(ProtocolConnections.devices), 1)
        assert CONTROLLER_NAME in ProtocolConnections.controllers

        self.assertEqual(len(ProtocolConnections.protocols), 2)
        self.assertEqual(ProtocolConnections.protocols[DEVICE_NAME],
                         self.proto_device)
        self.assertEqual(ProtocolConnections.protocols[CONTROLLER_NAME],
                         self.proto_controller)

    def test_device_connects_after_controller(self):

        EXPECTED_R_FOR_C = 'DL:' + END_LINE
        EXPECTED_R_FOR_C += 'DL:' + DEVICE_NAME + END_LINE
        EXPECTED_R_FOR_D = ''

        #controller is connecting
        C_REQUEST = 'CC:' + CONTROLLER_NAME + END_LINE
        self.proto_controller.dataReceived(C_REQUEST)

        #device is connecting
        D_REQUEST = 'DC:' + DEVICE_NAME + END_LINE
        self.proto_device.dataReceived(D_REQUEST)

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, EXPECTED_R_FOR_C)
        self.assertEqual(r_for_device, EXPECTED_R_FOR_D)

        self.assertEqual(len(ProtocolConnections.controllers), 1)
        self.assertEqual(len(ProtocolConnections.devices), 1)
        assert CONTROLLER_NAME in ProtocolConnections.controllers

        self.assertEqual(len(ProtocolConnections.protocols), 2)
        self.assertEqual(ProtocolConnections.protocols[DEVICE_NAME],
                         self.proto_device)
        self.assertEqual(ProtocolConnections.protocols[CONTROLLER_NAME],
                         self.proto_controller)

    def test_device_disconnects_after_controller_connects(self):

        EXPECTED_R_FOR_C = 'DL:' + DEVICE_NAME + END_LINE
        EXPECTED_R_FOR_C += 'DL:' + END_LINE
        EXPECTED_R_FOR_D = ''

        #device is connecting
        D_REQUEST = 'DC:' + DEVICE_NAME + END_LINE
        self.proto_device.dataReceived(D_REQUEST)

        #controller is connecting
        C_REQUEST = 'CC:' + CONTROLLER_NAME + END_LINE
        self.proto_controller.dataReceived(C_REQUEST)

        #device is disconnected
        self.proto_device.connectionLost('network failure')

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, EXPECTED_R_FOR_C)
        self.assertEqual(r_for_device, EXPECTED_R_FOR_D)

        self.assertEqual(len(ProtocolConnections.controllers), 1)
        self.assertEqual(len(ProtocolConnections.devices), 0)
        assert CONTROLLER_NAME in ProtocolConnections.controllers

        self.assertEqual(len(ProtocolConnections.protocols), 1)
        self.assertEqual(ProtocolConnections.protocols[CONTROLLER_NAME],
                         self.proto_controller)

    def test_controller_connects_to_device(self):
        EXPECTED_R_FOR_C = 'DL:' + DEVICE_NAME + END_LINE
        EXPECTED_R_FOR_C += 'DL:' + END_LINE
        EXPECTED_R_FOR_C += 'CD:OK' + END_LINE
        EXPECTED_R_FOR_D = ''

        #device is connecting
        DC_REQUEST = 'DC:' + DEVICE_NAME + END_LINE
        self.proto_device.dataReceived(DC_REQUEST)

        #controller is connecting
        CC_REQUEST = 'CC:' + CONTROLLER_NAME + END_LINE
        self.proto_controller.dataReceived(CC_REQUEST)

        #controller connects to selected device
        CD_REQUEST = 'CD:' + DEVICE_NAME + END_LINE
        self.proto_controller.dataReceived(CD_REQUEST)

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, EXPECTED_R_FOR_C)
        self.assertEqual(r_for_device, EXPECTED_R_FOR_D)

        self.assertEqual(len(ProtocolConnections.controllers), 1)
        self.assertEqual(len(ProtocolConnections.devices), 1)
        assert CONTROLLER_NAME in ProtocolConnections.controllers

        self.assertEqual(len(ProtocolConnections.protocols), 2)
        self.assertEqual(ProtocolConnections.protocols[DEVICE_NAME],
                         self.proto_device)
        self.assertEqual(ProtocolConnections.protocols[CONTROLLER_NAME],
                         self.proto_controller)

    def test_device_connected_to_controller_disconetcts(self):

        EXPECTED_R_FOR_C = 'DL:' + DEVICE_NAME + END_LINE
        EXPECTED_R_FOR_C += 'DL:' + END_LINE
        EXPECTED_R_FOR_C += 'CD:OK' + END_LINE
        EXPECTED_R_FOR_C += 'DD:' + END_LINE
        EXPECTED_R_FOR_C += 'DL:' + END_LINE

        EXPECTED_R_FOR_D = ''

        #device is connecting
        DC_REQUEST = 'DC:' + DEVICE_NAME + END_LINE
        self.proto_device.dataReceived(DC_REQUEST)

        #controller is connecting
        CC_REQUEST = 'CC:' + CONTROLLER_NAME + END_LINE
        self.proto_controller.dataReceived(CC_REQUEST)

        #controller connects to selected device
        CD_REQUEST = 'CD:' + DEVICE_NAME + END_LINE
        self.proto_controller.dataReceived(CD_REQUEST)

        #device is disconnected
        self.proto_device.connectionLost('network failure')

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, EXPECTED_R_FOR_C)
        self.assertEqual(r_for_device, EXPECTED_R_FOR_D)

        self.assertEqual(len(ProtocolConnections.controllers), 1)
        self.assertEqual(len(ProtocolConnections.devices), 0)
        assert CONTROLLER_NAME in ProtocolConnections.controllers

        self.assertEqual(len(ProtocolConnections.protocols), 1)
        self.assertEqual(ProtocolConnections.protocols[CONTROLLER_NAME],
                         self.proto_controller)

class ProtocolConnectionsRequestsTest(unittest.TestCase):

    def setUp(self):

        self.tr_device = proto_helpers.StringTransport()
        self.proto_device = ServerProtocol()
        self.proto_device.makeConnection(self.tr_device)

        self.proto_controller = ServerProtocol()
        self.tr_controller = proto_helpers.StringTransport()
        self.proto_controller.makeConnection(self.tr_controller)

        #device is connecting
        DC_REQUEST = 'DC:' + DEVICE_NAME + END_LINE
        self.proto_device.dataReceived(DC_REQUEST)

        #controller is connecting
        CC_REQUEST = 'CC:' + CONTROLLER_NAME + END_LINE
        self.proto_controller.dataReceived(CC_REQUEST)

        #controller connects to selected device
        CD_REQUEST = 'CD:' + DEVICE_NAME + END_LINE
        self.proto_controller.dataReceived(CD_REQUEST)

        self.expected_r_for_c = 'DL:' + DEVICE_NAME + END_LINE
        self.expected_r_for_c += 'DL:' + END_LINE
        self.expected_r_for_c += 'CD:OK' + END_LINE

        self.expected_r_for_d = ''

    def tearDown(self):
        ProtocolConnections.reset()

    def test_controller_sends_request_to_device(self):

        REQUEST = '0:0:0'

        # self.expected_r_for_c += '' + END_LINE

        self.expected_r_for_d += 'RE:' + REQUEST + END_LINE

        #controller send request
        CR_REQUEST = 'RE:' + REQUEST + END_LINE
        self.proto_controller.dataReceived(CR_REQUEST)

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, self.expected_r_for_c)
        self.assertEqual(r_for_device, self.expected_r_for_d)

    def test_device_sends_request_to_controller(self):

        REQUEST = '0:0:0'

        self.expected_r_for_c += 'RE:' + REQUEST + END_LINE

        #controller send request
        DR_REQUEST = 'RE:' + REQUEST + END_LINE
        self.proto_device.dataReceived(DR_REQUEST)

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, self.expected_r_for_c)
        self.assertEqual(r_for_device, self.expected_r_for_d)

    def test_device_sends_request_to_controller_no_enpoint_error(self):

        REQUEST = '0:0:0'

        self.expected_r_for_d += 'SE:E_20' + END_LINE

        #controller disconnects
        self.proto_controller.connectionLost('network failure')

        #device send request
        DR_REQUEST = 'RE:' + REQUEST + END_LINE
        self.proto_device.dataReceived(DR_REQUEST)

        r_for_controller = self.tr_controller.value()
        r_for_device = self.tr_device.value()

        self.assertEqual(r_for_controller, self.expected_r_for_c)
        self.assertEqual(r_for_device, self.expected_r_for_d)


def proto_factory():
    proto = ServerProtocol()
    tr = proto_helpers.StringTransport()
    proto.makeConnection(tr)

    return proto, tr


class ProtocolConnectionsUnitsTest(unittest.TestCase):

    def tearDown(self):
        ProtocolConnections.reset()

    def test_get_available_devices(self):

        avail_devs = ProtocolConnections.get_available_devices()
        assert avail_devs == []

        DEV1_NAME = 'mock-dev1'
        proto_d_1, _ = proto_factory()
        DEV2_NAME = 'mock-dev2'
        proto_d_2, _ = proto_factory()
        DEV3_NAME = 'mock-dev3'
        proto_d_3, _ = proto_factory()
        CON1_NAME = 'mock-con1'
        proto_c_1, _ = proto_factory()

        ProtocolConnections.connect_device(proto_d_1, DEV1_NAME)
        avail_devs = ProtocolConnections.get_available_devices()
        assert DEV1_NAME in avail_devs
        assert len(avail_devs) == 1

        ProtocolConnections.connect_device(proto_d_2, DEV2_NAME)
        avail_devs = ProtocolConnections.get_available_devices()
        assert DEV1_NAME in avail_devs
        assert DEV2_NAME in avail_devs
        assert len(avail_devs) == 2

        ProtocolConnections.connect_device(proto_d_3, DEV3_NAME)
        avail_devs = ProtocolConnections.get_available_devices()
        assert DEV1_NAME in avail_devs
        assert DEV2_NAME in avail_devs
        assert DEV3_NAME in avail_devs
        assert len(avail_devs) == 3

        ProtocolConnections.connect_controller(proto_c_1, CON1_NAME)
        ProtocolConnections.make_connection(proto_d_1, proto_c_1)
        avail_devs = ProtocolConnections.get_available_devices()
        assert DEV2_NAME in avail_devs
        assert DEV3_NAME in avail_devs
        assert len(avail_devs) == 2

        ProtocolConnections.disconnect_protocol(proto_c_1)
        avail_devs = ProtocolConnections.get_available_devices()
        assert DEV1_NAME in avail_devs
        assert DEV2_NAME in avail_devs
        assert DEV3_NAME in avail_devs
        assert len(avail_devs) == 3

    def test_connect_device(self):

        DEVICE_NAME = 'mock-dev'
        proto_dev, _ = proto_factory()

        CONTROLLER_NAME = 'mock-con'
        proto_con, tr_con = proto_factory()

        EXPECTED_R_FOR_C = 'DL:' + END_LINE
        EXPECTED_R_FOR_C += 'DL:' + DEVICE_NAME + END_LINE

        assert len(ProtocolConnections.devices) == 0
        assert len(ProtocolConnections.protocols) == 0

        ProtocolConnections.connect_controller(proto_con, CONTROLLER_NAME)
        ProtocolConnections.connect_device(proto_dev, DEVICE_NAME)

        assert len(ProtocolConnections.devices) == 1
        assert len(ProtocolConnections.protocols) == 2
        assert DEVICE_NAME in ProtocolConnections.devices
        assert proto_dev == ProtocolConnections.protocols[DEVICE_NAME]

        #make sure connected controllers get notified about new device
        resp_for_controller = tr_con.value()
        assert resp_for_controller == EXPECTED_R_FOR_C
