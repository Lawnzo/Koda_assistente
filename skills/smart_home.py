import tinytuya
from skills.base_skill import BaseSkill

class SmartHomeSkill(BaseSkill):
    def can_handle(self, intent):
        return intent in ["LUZ", "VENTILADOR"]

    def execute(self, intent, command_text):
        if intent == "LUZ":
            return self.control_light(command_text)
        elif intent == "VENTILADOR":
            return self.control_fan(command_text)
        return None, "SYS_ERR"

    def resolve_device_ip(self, target_dev_id):
        """
        Varre a rede local automaticamente se o IP configurado tiver mudado no roteador.
        """
        try:
            print(f"[TUYA AUTO-DISCOVERY] Procurando novo IP para o dispositivo {target_dev_id}...")
            devices = tinytuya.deviceScan(verbose=False)
            for ip, info in devices.items():
                if info.get('id') == target_dev_id or info.get('gwId') == target_dev_id:
                    print(f"[TUYA AUTO-DISCOVERY] Novo IP encontrado: {ip}")
                    return ip
        except Exception as e:
            print(f"[TUYA DISCOVERY WARN] Falha na busca de IP: {e}")
        return None

    def control_light(self, cmd):
        if not self.config or not hasattr(self.config, 'LUZ_ID'):
            return "Configurações da lâmpada não encontradas.", "ERRO_HARDWARE"

        current_ip = getattr(self.config, 'LUZ_IP', '192.168.0.4')
        dev_id = self.config.LUZ_ID
        key = self.config.LUZ_KEY
        version = getattr(self.config, 'LUZ_VERSAO', 3.3)

        cmd_lower = cmd.lower()
        is_off = any(x in cmd_lower for x in ["desliga", "apaga", "desligar", "apagar", "desligue", "apague", "desativar", "escuro", "parar", "mudo"])

        try:
            d = tinytuya.BulbDevice(dev_id=dev_id, address=current_ip, local_key=key, version=version)
            d.set_socketPersistent(True)

            if is_off:
                print(f"[TUYA LUZ] Executando desligamento da lâmpada em {current_ip}...")
                ok_off = False
                try:
                    d.turn_off()
                    ok_off = True
                except Exception as e_off:
                    print(f"[TUYA WARN turn_off] {e_off}")

                try:
                    d.set_value(20, False)
                    ok_off = True
                except Exception as e_val:
                    print(f"[TUYA WARN set_value 20] {e_val}")

                if ok_off:
                    return "Entendido, apagando a luz do quarto.", "HARDWARE_LUZ"
            else:
                print(f"[TUYA LUZ] Executando acionamento da lâmpada em {current_ip}...")
                ok_on = False
                try:
                    d.turn_on()
                    ok_on = True
                except Exception as e_on:
                    print(f"[TUYA WARN turn_on] {e_on}")

                try:
                    d.set_value(20, True)
                    ok_on = True
                except Exception as e_val:
                    print(f"[TUYA WARN set_value 20] {e_val}")

                if ok_on:
                    return "Luz do quarto acesa.", "HARDWARE_LUZ"

        except Exception as e:
            print(f"[TUYA ERRO LUZ IP {current_ip}] {e}. Tentando descoberta automática de IP...")
            new_ip = self.resolve_device_ip(dev_id)
            if new_ip:
                try:
                    self.config.LUZ_IP = new_ip
                    d = tinytuya.BulbDevice(dev_id=dev_id, address=new_ip, local_key=key, version=version)
                    d.set_socketPersistent(True)
                    if is_off:
                        d.turn_off()
                        return "Entendido, apagando a luz.", "HARDWARE_LUZ"
                    else:
                        d.turn_on()
                        return "Luz do quarto acesa.", "HARDWARE_LUZ"
                except Exception as ex:
                    print(f"[TUYA ERRO RETRY LUZ] {ex}")

        return "Lucas, perdi a comunicação local com a lâmpada.", "ERRO_HARDWARE"

    def control_fan(self, cmd):
        if not self.config or not hasattr(self.config, 'VENT_ID'):
            return "Configurações do ventilador não encontradas.", "ERRO_HARDWARE"

        current_ip = getattr(self.config, 'VENT_IP', '192.168.0.3')
        dev_id = self.config.VENT_ID
        key = self.config.VENT_KEY
        version = getattr(self.config, 'VENT_VERSAO', 3.3)

        cmd_lower = cmd.lower()
        is_off = any(x in cmd_lower for x in ["desliga", "desligar", "desligue", "apaga", "apagar", "apague", "desativar", "parar"])

        try:
            d = tinytuya.OutletDevice(dev_id=dev_id, address=current_ip, local_key=key, version=version)
            d.set_socketPersistent(True)

            if is_off:
                d.turn_off()
                return "Tudo bem. Desligando o ventilador.", "HARDWARE_VENT"
            else:
                d.turn_on()
                return "Entendido. Ligando o ventilador.", "HARDWARE_VENT"

        except Exception as e:
            print(f"[TUYA ERRO VENT IP {current_ip}] {e}. Tentando descoberta automática...")
            new_ip = self.resolve_device_ip(dev_id)
            if new_ip:
                try:
                    self.config.VENT_IP = new_ip
                    d = tinytuya.OutletDevice(dev_id=dev_id, address=new_ip, local_key=key, version=version)
                    d.set_socketPersistent(True)
                    if is_off:
                        d.turn_off()
                        return "Desligando o ventilador.", "HARDWARE_VENT"
                    else:
                        d.turn_on()
                        return "Ligando o ventilador.", "HARDWARE_VENT"
                except Exception as ex:
                    print(f"[TUYA ERRO RETRY VENT] {ex}")

            return "Lucas, não consegui me conectar ao ventilador.", "ERRO_HARDWARE"
