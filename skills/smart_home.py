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
            print(f"[TUYA LUZ] Conectando ao BulbDevice em {current_ip} [ver {version}]...")
            d = tinytuya.BulbDevice(dev_id=dev_id, address=current_ip, local_key=key, version=version)
            d.set_socketPersistent(False)

            if is_off:
                print(f"[TUYA LUZ] Desligando lâmpada...")
                # Envia comandos diretos sem persistência de socket para evitar socket lock
                res1 = d.turn_off()
                res2 = d.set_value(20, False)
                print(f"[TUYA LUZ RES OFF] turn_off: {res1} | set_value: {res2}")
                return "Entendido, apagando a luz do quarto.", "HARDWARE_LUZ"
            else:
                print(f"[TUYA LUZ] Acendendo lâmpada...")
                res1 = d.turn_on()
                res2 = d.set_value(20, True)
                print(f"[TUYA LUZ RES ON] turn_on: {res1} | set_value: {res2}")
                return "Luz do quarto acesa.", "HARDWARE_LUZ"

        except Exception as e:
            err_msg = str(e)
            print(f"[TUYA ERRO LUZ IP {current_ip}] {err_msg}. Tentando descoberta automática de IP...")
            new_ip = self.resolve_device_ip(dev_id)
            if new_ip:
                try:
                    self.config.LUZ_IP = new_ip
                    d = tinytuya.BulbDevice(dev_id=dev_id, address=new_ip, local_key=key, version=version)
                    d.set_socketPersistent(False)
                    if is_off:
                        d.turn_off()
                        return "Entendido, apagando a luz.", "HARDWARE_LUZ"
                    else:
                        d.turn_on()
                        return "Luz do quarto acesa.", "HARDWARE_LUZ"
                except Exception as ex:
                    print(f"[TUYA ERRO RETRY LUZ] {ex}")
                    return f"Erro na conexão Tuya: {str(ex)[:30]}", "ERRO_HARDWARE"

            return f"Erro ao acessar lâmpada: {err_msg[:30]}", "ERRO_HARDWARE"

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
            d.set_socketPersistent(False)

            if is_off:
                d.turn_off()
                return "Tudo bem. Desligando o ventilador.", "HARDWARE_VENT"
            else:
                d.turn_on()
                return "Entendido. Ligando o ventilador.", "HARDWARE_VENT"

        except Exception as e:
            err_msg = str(e)
            print(f"[TUYA ERRO VENT IP {current_ip}] {err_msg}. Tentando descoberta automática...")
            new_ip = self.resolve_device_ip(dev_id)
            if new_ip:
                try:
                    self.config.VENT_IP = new_ip
                    d = tinytuya.OutletDevice(dev_id=dev_id, address=new_ip, local_key=key, version=version)
                    d.set_socketPersistent(False)
                    if is_off:
                        d.turn_off()
                        return "Desligando o ventilador.", "HARDWARE_VENT"
                    else:
                        d.turn_on()
                        return "Ligando o ventilador.", "HARDWARE_VENT"
                except Exception as ex:
                    print(f"[TUYA ERRO RETRY VENT] {ex}")

            return f"Erro no ventilador: {err_msg[:30]}", "ERRO_HARDWARE"
