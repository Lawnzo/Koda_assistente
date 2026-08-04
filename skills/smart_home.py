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
            import socket
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(3)
            devices = tinytuya.deviceScan(verbose=False, maxretry=1)
            socket.setdefaulttimeout(old_timeout)
            
            for ip, info in devices.items():
                if info.get('id') == target_dev_id or info.get('gwId') == target_dev_id:
                    print(f"[TUYA AUTO-DISCOVERY] Novo IP encontrado: {ip}")
                    return ip
        except Exception as e:
            print(f"[TUYA DISCOVERY WARN] Falha na busca de IP: {e}")
            import socket
            try:
                socket.setdefaulttimeout(old_timeout)
            except:
                pass
        return None

    def _tuya_action(self, dev_id, address, key, version, is_off, is_bulb=True):
        import tinytuya
        if is_bulb:
            d = tinytuya.BulbDevice(dev_id=dev_id, address=address, local_key=key, version=version)
        else:
            d = tinytuya.OutletDevice(dev_id=dev_id, address=address, local_key=key, version=version)
            
        d.set_socketPersistent(False)
        d.set_socketTimeout(2)
        if is_off:
            d.turn_off()
        else:
            d.turn_on()
        return True

    def control_light(self, cmd):
        if not self.config or not hasattr(self.config, 'LUZ_ID'):
            return "Configurações da lâmpada não encontradas.", "ERRO_HARDWARE"

        current_ip = getattr(self.config, 'LUZ_IP', '192.168.0.4')
        dev_id = self.config.LUZ_ID
        key = self.config.LUZ_KEY
        version = getattr(self.config, 'LUZ_VERSAO', 3.3)

        cmd_lower = cmd.lower()
        is_off = any(x in cmd_lower for x in ["desliga", "apaga", "desligar", "apagar", "desligue", "apague", "desativar", "escuro", "parar", "mudo"])

        import concurrent.futures
        
        try:
            print(f"[TUYA LUZ] Executando comando na lâmpada em {current_ip}...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._tuya_action, dev_id, current_ip, key, version, is_off, True)
                future.result(timeout=4) # Timeout Rígido Absoluto de 4 Segundos
                
            msg = "Entendido, apagando a luz." if is_off else "Luz do quarto acesa."
            return msg, "HARDWARE_LUZ"
            
        except Exception as e:
            err_msg = str(e)
            print(f"[TUYA ERRO LUZ IP {current_ip}] Timeout/Falha: {err_msg[:20]}. Buscando novo IP...")
            new_ip = self.resolve_device_ip(dev_id)
            if new_ip:
                try:
                    self.config.LUZ_IP = new_ip
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._tuya_action, dev_id, new_ip, key, version, is_off, True)
                        future.result(timeout=4)
                        
                    msg = "Entendido, apagando a luz." if is_off else "Luz do quarto acesa."
                    return msg, "HARDWARE_LUZ"
                except Exception as ex:
                    print(f"[TUYA ERRO RETRY LUZ] {ex}")
                    return f"Erro na conexão Tuya. Tente mais tarde.", "ERRO_HARDWARE"

            return f"Erro ao acessar lâmpada. A rede pode estar fora do ar.", "ERRO_HARDWARE"

    def control_fan(self, cmd):
        if not self.config or not hasattr(self.config, 'VENT_ID'):
            return "Configurações do ventilador não encontradas.", "ERRO_HARDWARE"

        current_ip = getattr(self.config, 'VENT_IP', '192.168.0.3')
        dev_id = self.config.VENT_ID
        key = self.config.VENT_KEY
        version = getattr(self.config, 'VENT_VERSAO', 3.3)

        cmd_lower = cmd.lower()
        is_off = any(x in cmd_lower for x in ["desliga", "desligar", "desligue", "apaga", "apagar", "apague", "desativar", "parar"])

        import concurrent.futures
        
        try:
            print(f"[TUYA VENT] Executando comando no ventilador em {current_ip}...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._tuya_action, dev_id, current_ip, key, version, is_off, False)
                future.result(timeout=4)
                
            msg = "Desligando o ventilador." if is_off else "Ligando o ventilador."
            return msg, "HARDWARE_VENT"

        except Exception as e:
            err_msg = str(e)
            print(f"[TUYA ERRO VENT IP {current_ip}] Timeout/Falha: {err_msg[:20]}. Buscando novo IP...")
            new_ip = self.resolve_device_ip(dev_id)
            if new_ip:
                try:
                    self.config.VENT_IP = new_ip
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._tuya_action, dev_id, new_ip, key, version, is_off, False)
                        future.result(timeout=4)
                        
                    msg = "Desligando o ventilador." if is_off else "Ligando o ventilador."
                    return msg, "HARDWARE_VENT"
                except Exception as ex:
                    print(f"[TUYA ERRO RETRY VENT] {ex}")
                    return f"Erro na conexão Tuya. Tente mais tarde.", "ERRO_HARDWARE"

            return f"Erro ao acessar ventilador. A rede pode estar fora do ar.", "ERRO_HARDWARE"
