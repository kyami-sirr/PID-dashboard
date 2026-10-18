import time

class PIDEngine:
    def __init__(self):
        self.ppr = 210.0
        self.current_mode = 0
        self.setpoint = 0.0

        self.last_pulses = 0
        self.last_calc_time = time.time()

        self.kp_s, self.ki_s, self.kd_s = 0.45, 0.12, 0.002
        self.integral_s = 0.0
        self.filtered_rpm = 0.0
        self.last_rpm = 0.0

        self.kp_p, self.ki_p, self.kd_p = 0.85, 0.01, 0.05
        self.integral_p = 0.0
        self.last_err_p = 0.0

        self.smoothed_pwm = 0.0
        self.MIN_PWM_DEADBAND = 18
        self.MAX_PWM_LIMIT = 255

    def set_pid_gains(self, mode, kp, ki, kd):
        if mode in (2, 3):
            self.kp_s, self.ki_s, self.kd_s = kp, ki, kd
        elif mode in (4, 5):
            self.kp_p, self.ki_p, self.kd_p = kp, ki, kd

    def process(self, raw_pulses):
        now = time.time()
        dt = now - self.last_calc_time
        if dt <= 0.001 or dt > 0.5:
            dt = 0.05
        self.last_calc_time = now

        delta_pulses = raw_pulses - self.last_pulses
        self.last_pulses = raw_pulses

        base_ppr = float(self.ppr) if self.ppr > 0 else 210.0
        effective_ppr = base_ppr * 4.0
        
        raw_rpm = (delta_pulses / effective_ppr) / dt * 60.0
        self.filtered_rpm = (0.80 * self.filtered_rpm) + (0.20 * raw_rpm)
        measured_deg = (raw_pulses / effective_ppr) * 360.0

        target_pwm = 0
        direction = 0
        actual_val = 0.0

        if self.current_mode == 0:
            actual_val = measured_deg
            self.integral_s = 0.0
            self.integral_p = 0.0
            return actual_val, 0, 0

        elif self.current_mode == 1:
            actual_val = self.filtered_rpm
            target_pwm = abs(int(self.setpoint))
            direction = 1 if self.setpoint > 0 else (-1 if self.setpoint < 0 else 0)

        elif self.current_mode in (2, 3):
            actual_val = self.filtered_rpm
            err = self.setpoint - self.filtered_rpm

            if self.ki_s > 0:
                self.integral_s += err * dt
                max_i = 150.0 / self.ki_s
                self.integral_s = max(-max_i, min(max_i, self.integral_s))
            else:
                self.integral_s = 0.0

            deriv = (self.filtered_rpm - self.last_rpm) / dt
            self.last_rpm = self.filtered_rpm

            u = (self.kp_s * err) + (self.ki_s * self.integral_s) - (self.kd_s * deriv)
            direction = 1 if u > 0 else (-1 if u < 0 else 0)
            calc_p = int(abs(u))

            target_pwm = max(self.MIN_PWM_DEADBAND, min(self.MAX_PWM_LIMIT, calc_p)) if self.setpoint != 0 else 0

        elif self.current_mode in (4, 5):
            actual_val = measured_deg
            err = self.setpoint - measured_deg

            if abs(err) <= 1.0:
                target_pwm = 0
                direction = 0
                self.integral_p = 0.0
            else:
                if self.ki_p > 0:
                    self.integral_p += err * dt
                    max_ip = 100.0 / self.ki_p
                    self.integral_p = max(-max_ip, min(max_ip, self.integral_p))
                
                deriv = (err - self.last_err_p) / dt
                u = (self.kp_p * err) + (self.ki_p * self.integral_p) + (self.kd_p * deriv)
                direction = 1 if u >= 0 else -1
                target_pwm = max(self.MIN_PWM_DEADBAND, min(190, int(abs(u))))
            
            self.last_err_p = err

        return actual_val, target_pwm, direction
