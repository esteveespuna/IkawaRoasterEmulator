import IkawaCmd.protc_pb2 as ikawaCmd_pb2
import roaster_helper_libs
import pandas as pd
import os


class RoasterState():
    def __init__(self):
        self.time = 0
        self.fan = int(50 * 2.55)
        self.fan_measured = int(50 * 12 / 60)

        self.simulating_roast = False
        self.simulating_roast_timer = 0
        self.start_roast_file =  "./sim_session_exp3_feb26.csv" #"./decaf_session.csv"
        self.simulation_command_file = "./simulate"
        self.start_roast_file_index = 0
        self.simulated_roast_data = pd.DataFrame()

        """
        IDLE(0), PRE_HEAT(1), READY_FOR_ROAST(2), ROASTING(3), BUSY(4),  COOLDOWN(5),  DOSER_OPEN(6), ERROR(7), READY_TO_BLOWOVER(8), TEST_MODE(9);
        """
        if (os.path.isfile(self.start_roast_file)):
            self.simulated_roast_data = pd.read_csv(self.start_roast_file).dropna(axis=1).astype(int)
            self.simulated_roast_data.columns = list(
                map(lambda x: x[1:] if x[0] == ' ' else x, self.simulated_roast_data.columns))

            self.state_from_simulation_idx(self.start_roast_file_index)
        else:
            print("No file found: " + self.start_roast_file)

            self.time = 0
            self.temp_above = 0
            self.fan = 0
            self.state = 0
            self.heater = 0
            self.p = 0
            self.i = 0
            self.d = 0
            self.setpoint = 0
            self.fan_measured = 0
            self.board_temp = 0
            self.temp_below = 0
            self.fan_rpm_measured = 0
            self.fan_rpm_setpoint = 0
            self.fan_i = 0
            self.fan_p = 0
            self.fan_d = 0
            self.fan_power = 0

            self.j = 0
            self.relay_state = 0
            self.pid_sensor = 0

            self.temp_above_filtered = 0
            self.temp_below_filtered = 0
            self.ror_above = 0
            self.ror_below = 0

        print("Initializing RoasterState")

        """ required fields
                   roasterStatus.time = respMachStatusGetAll.getTime() / 10.0f;
                   roasterStatus.fanSet = respMachStatusGetAll.getFan() / 2.55f;
                   roasterStatus.fanSpeed = (int) ((respMachStatusGetAll.getFanMeasured() / 12.0f) * 60.0f);
                   roasterStatus.state = respMachStatusGetAll.getState();
                   roasterStatus.heater = respMachStatusGetAll.getHeater() * 2;
                   roasterStatus.p = respMachStatusGetAll.getP() / 10.0f;
                   roasterStatus.i = respMachStatusGetAll.getI() / 10.0f;
                   roasterStatus.d = respMachStatusGetAll.getD() / 10.0f;
                   roasterStatus.setpoint = respMachStatusGetAll.getSetpoint() / 10.0f;
                   """

    def next_step(self):
        if (os.path.isfile(self.simulation_command_file)):

            if self.start_roast_file_index >= len(self.simulated_roast_data) :
                self.start_roast_file_index = 0
                os.remove(self.simulation_command_file)

            else:
                self.start_roast_file_index = self.start_roast_file_index + 5
        else:
            self.start_roast_file_index = 0

        self.state_from_simulation_idx(self.start_roast_file_index)



    def state_from_simulation_idx(self, idx):
        self.time = self.simulated_roast_data.iloc[idx]['time']
        self.temp_above = self.simulated_roast_data.iloc[idx]['temp_above']
        self.fan = self.simulated_roast_data.iloc[idx]['fan']
        self.state = self.simulated_roast_data.iloc[idx]['state']
        self.heater = self.simulated_roast_data.iloc[idx]['heater']
        self.p = self.simulated_roast_data.iloc[idx]['p']
        self.i = self.simulated_roast_data.iloc[idx]['i']
        self.d = self.simulated_roast_data.iloc[idx]['d']
        self.setpoint = self.simulated_roast_data.iloc[idx]['setpoint']
        self.fan_measured = self.simulated_roast_data.iloc[idx]['fan_measured']
        self.board_temp = self.simulated_roast_data.iloc[idx]['board_temp']
        self.temp_below = self.simulated_roast_data.iloc[idx]['temp_below']
        self.fan_rpm_measured = self.simulated_roast_data.iloc[idx]['fan_rpm_measured']
        self.fan_rpm_setpoint = self.simulated_roast_data.iloc[idx]['fan_rpm_setpoint']
        self.fan_i = self.simulated_roast_data.iloc[idx]['fan_i']
        self.fan_p = self.simulated_roast_data.iloc[idx]['fan_p']
        self.fan_d = self.simulated_roast_data.iloc[idx]['fan_d']
        self.fan_power = self.simulated_roast_data.iloc[idx]['fan_power']

        self.j = self.simulated_roast_data.iloc[idx]['j']
        self.relay_state = self.simulated_roast_data.iloc[idx]['relay_state']
        self.pid_sensor = self.simulated_roast_data.iloc[idx]['pid_sensor']

        self.temp_above_filtered = self.simulated_roast_data.iloc[idx]['temp_above_filtered']
        self.temp_below_filtered = self.simulated_roast_data.iloc[idx]['temp_below_filtered']
        self.ror_above = self.simulated_roast_data.iloc[idx]['ror_above']
        self.ror_below = self.simulated_roast_data.iloc[idx]['ror_below']


class IkawaEmulatedRoaster():
    ###CmdType
    MACH_PROP_GET_TYPE = 2
    MACH_PROP_GET_ID = 3
    MACH_PROP_GET_SUPPORT_INFO = 23
    BOOTLOADER_GET_VERSION = 0
    HIST_GET_TOTAL_ROAST_COUNT = 13
    SETTING_GET = 17

    PROFILE_GET = 15
    PROFILE_SET = 16
    MACH_STATUS_GET_ERROR_VALUE = 10
    MACH_STATUS_GET_ALL_VALUE = 11

    def __init__(self):
        self.roaster = RoasterState()

    def process_command_from_app(self, message):
        try:
            IkawaApp_decoded_message = ikawaCmd_pb2.Message().FromString(message)
            print(" seq: %d cmd_type %d" % (IkawaApp_decoded_message.seq, IkawaApp_decoded_message.cmd_type))

        except Exception as e:
            print("Error: Invalid Message Serialize ProtoBuf")
            print(e)
            return None

        respType = ikawaCmd_pb2.IkawaResponse()

        respType.seq = IkawaApp_decoded_message.seq
        respType.resp = 1  ## OK

        try:
            if IkawaApp_decoded_message.cmd_type == self.MACH_PROP_GET_TYPE:
                # Works Ok
                print("CMD MACH_PROP_GET_TYPE %d" % (self.MACH_PROP_GET_TYPE))
                respType.resp_mach_prop_type.type_ = 3  # de v1 a v4
                respType.resp_mach_prop_type.variant = 0  # PRO(0),HOME(3);

            if IkawaApp_decoded_message.cmd_type == self.MACH_PROP_GET_ID:
                print("CMD MACH_PROP_GET_ID %d" % (self.MACH_PROP_GET_ID))
                # Works Ok
                respType.resp_mach_id.id_ = 800368

            if IkawaApp_decoded_message.cmd_type == self.MACH_PROP_GET_SUPPORT_INFO:
                print("CMD MACH_PROP_GET_SUPPORT_INFO %d" % (self.MACH_PROP_GET_SUPPORT_INFO))
                respType.resp_mach_prop_get_support_info.profile_schema = 2

            if IkawaApp_decoded_message.cmd_type == self.BOOTLOADER_GET_VERSION:
                print("CMD BOOTLOADER_GET_VERSION %d" % (self.BOOTLOADER_GET_VERSION))
                # Works Ok
                respType.resp_bootloader_get_version.version = 25  # 25 is last version
                respType.resp_bootloader_get_version.revision = "17-g1925dbd-DIRTY"  # 17-g1925dbd is last revision

            if IkawaApp_decoded_message.cmd_type == self.HIST_GET_TOTAL_ROAST_COUNT:
                print("CMD HIST_GET_TOTAL_ROAST_COUNT %d" % (self.HIST_GET_TOTAL_ROAST_COUNT))
                # Works Ok
                respType.resp_hist_get_total_roast_count.total_roast_count = 5

            if IkawaApp_decoded_message.cmd_type == self.PROFILE_SET:
                print("CMD PROFILE_SET %d" % (self.PROFILE_SET))

                recv_profile = roaster_helper_libs.RoastProfile()
                recv_profile.from_proto(IkawaApp_decoded_message)
                recv_profile.display_roast_profile()
                recv_profile.toJsonFile("profile_set.json")

                # Works Ok

            if IkawaApp_decoded_message.cmd_type == self.PROFILE_GET:
                print("CMD PROFILE_GET %d" % (self.PROFILE_GET))
                last_roast_profile = roaster_helper_libs.RoastProfile()
                last_roast_profile.from_json("profile_get.json")
                last_roast_profile.display_roast_profile()
                respType = last_roast_profile.toProtoBuf(IkawaApp_decoded_message.seq)

            if IkawaApp_decoded_message.cmd_type == self.MACH_STATUS_GET_ERROR_VALUE:
                print("CMD MACH_STATUS_GET_ERROR_VALUE %d" % (self.MACH_STATUS_GET_ERROR_VALUE))
                respType.resp_mach_status_get_error.error = 1

            ### private void processStatus(Ikawa.RespMachStatusGetAll respMachStatusGetAll) {
            if IkawaApp_decoded_message.cmd_type == self.MACH_STATUS_GET_ALL_VALUE:
                print("CMD MACH_STATUS_GET_ALL_VALUE %d" % (self.MACH_STATUS_GET_ALL_VALUE))
                respType.resp_mach_status_get_all.time = self.roaster.time
                respType.resp_mach_status_get_all.temp_above = self.roaster.temp_above
                respType.resp_mach_status_get_all.fan = self.roaster.fan
                respType.resp_mach_status_get_all.state = self.roaster.state  # 0 Idle (ready to roast) 1 Pre-heating
                respType.resp_mach_status_get_all.heater = self.roaster.heater

                respType.resp_mach_status_get_all.p = self.roaster.p
                respType.resp_mach_status_get_all.i = self.roaster.i
                respType.resp_mach_status_get_all.d = self.roaster.d
                respType.resp_mach_status_get_all.fan_measured = self.roaster.fan_measured
                respType.resp_mach_status_get_all.setpoint = self.roaster.setpoint

                respType.resp_mach_status_get_all.fan_i = self.roaster.fan_i
                respType.resp_mach_status_get_all.fan_p = self.roaster.fan_p
                respType.resp_mach_status_get_all.fan_d = self.roaster.fan_d

                respType.resp_mach_status_get_all.fan_power = self.roaster.fan_power
                respType.resp_mach_status_get_all.j = self.roaster.j
                respType.resp_mach_status_get_all.relay_state = self.roaster.relay_state
                respType.resp_mach_status_get_all.pid_sensor = self.roaster.pid_sensor
                respType.resp_mach_status_get_all.temp_above_filtered = self.roaster.temp_above_filtered

                respType.resp_mach_status_get_all.temp_below_filtered = self.roaster.temp_below_filtered
                respType.resp_mach_status_get_all.ror_above = self.roaster.ror_above
                respType.resp_mach_status_get_all.ror_below = self.roaster.ror_below

                respType.resp_mach_status_get_all.temp_below = self.roaster.temp_below
                ### If we are simulating do next step
                self.roaster.next_step()

                #
                if self.roaster.state > 0:
                    respType.resp_mach_status_get_all.temp_above_filtered = self.roaster.temp_above_filtered
                    respType.resp_mach_status_get_all.temp_below_filtered = self.roaster.temp_below_filtered
                    respType.resp_mach_status_get_all.fan_power = self.roaster.fan_power

            ### Roaster Helper Public static Profile convertToRoasterProfile(ProfileItem profileItem) {
            if IkawaApp_decoded_message.cmd_type == self.SETTING_GET:
                """  Bootloader Version 25, 17-g1925d8d-DIRTY 
                Total Roast Count 27 
                Error value 1 
                Settings 
                Roast count 27 
                Roaster voltage 230 
                Above sensor type 1 
                Heater power 3 
                Time multiplier 0 
                Fan control 0 
                Last service date 0 
                Roastcount since service 27
                 public enum RoasterSettingId {
                    ROAST_COUNT(24),
                    ROASTER_VOLTAGE(153),
                    ABOVE_SENSOR_TYPE(154),
                    HEATER_POWER(155),
                    TIME_MULTIPLIER(158),
                    FAN_CONTROL(171),
                    LAST_SERVICE_DATE(174),
                    ROASTCOUNT_SINCE_SERVICE(175);
                """
                requested_field = IkawaApp_decoded_message.setting_get.field
                print("CMD SETTING_GET %d field: %d" % (self.SETTING_GET, requested_field))
                respType.resp_setting_get.field = requested_field

                if requested_field == 24:  # ROAST_COUNT
                    respType.resp_setting_get.field = 5
                if requested_field == 153:  # ROASTER_VOLTAGE
                    respType.resp_setting_get.field = 230

                if requested_field == 154:  # ABOVE_SENSOR_TYPE
                    """UNSET(0),
                    FAST(1),
                    ROBUST(2);"""
                    respType.resp_setting_get.field = 1

                if requested_field == 155:  # HEATER_POWER
                    respType.resp_setting_get.field = 3

                if requested_field == 158:  # TIME_MULTIPLIER
                    respType.resp_setting_get.field = 0
                if requested_field == 171:  # FAN_CONTROL
                    respType.resp_setting_get.field = 0
                if requested_field == 174:  # LAST_SERVICE_DATE
                    respType.resp_setting_get.field = 0

                if requested_field == 175:  # ROAST COUNT SINCE SERVICE
                    respType.resp_setting_get.field = 5




        except Exception as e:
            print("Error: Invalid Message")
            print(e)
            return None

        return respType
