# -*- coding: utf-8 -*-
"""
Created on Sun Aug 25 20:42:02 2019

@author: tiarl
"""

def getPolyFromPoints(x_axis, y_axis, deg=3):
    '''
    Create a polynomial using the x_axis and y_axis points with deg number of
    degrees.
    '''
    import numpy as np
    return np.poly1d(np.polyfit(x_axis, y_axis, deg))


def detectCommutation(pwm_signal):
    '''
    Detect the commutation of the digital pwm_signal [0, 1] where:
        * 1 is a positive commutation;
        * -1 is a negative commutation;
        * 0 is a constant state.
    
    Parameters
    ----------
    pwm_signal: numpy.array
        A numpy.array with values 1 and 0 only.
    
    Return
    ------
    diff: numpy.array
        The vector with the detected commutations
    '''
    y1 = pwm_signal[:-1]
    y2 = pwm_signal[1:]
    
    diff = y2 - y1
    
    return diff


def switchingLosesHalfBridge(switch_s1, current, duration, pol_eon, pol_eoff, 
                             pol_erec, pol_eDon, verbate=True):
    '''
    Table with Switching Losses for a half-bridge inverter (2-levels).
    
    Parameters
    ----------
    switch_s1: numpy.array
        Is the digital PWM command of the top leg switch of the inverter.   
    current: numpy.array
        Is the current measurment array. Generally is the phase out current of 
        the converter.
    duration: float
        The total duration time of simulation. (Final Time - Initial time)
        
    p_on, p_off, p_rec, p_Don : numpy.poly1d type
        Is the losses polynomials for each commutation type of 
        the semiconductors presente in a half-bridge inverter.
        
    '''
    import numpy as np
    
    commut = detectCommutation(switch_s1)
    
    commut_pos = commut == 1
    commut_neg = commut == -1
    
    current0 = current[1:]
    
    current_pos = current0 >= 0
    current_neg = current0 < 0
    
    comut_neg_cur_pos = commut_neg * current_pos
    comut_neg_cur_neg = commut_neg * current_neg
    comut_pos_cur_pos = commut_pos * current_pos
    comut_pos_cur_neg = commut_pos * current_neg
    
    current_comut_neg_cur_pos = np.abs(current0[comut_neg_cur_pos])
    current_comut_neg_cur_neg = np.abs(current0[comut_neg_cur_neg])
    current_comut_pos_cur_pos = np.abs(current0[comut_pos_cur_pos])
    current_comut_pos_cur_neg = np.abs(current0[comut_pos_cur_neg])
    
    # For 'S1'
    s1_eoff = pol_eoff(current_comut_neg_cur_pos)
    s1_eon = pol_eon(current_comut_pos_cur_pos)
    
    # For 'S2'
    s2_eoff = pol_eoff(current_comut_pos_cur_neg)
    s2_eon = pol_eon(current_comut_neg_cur_neg)
    
    # For 'D1'
    d1_rec = pol_erec(current_comut_neg_cur_neg)
    d1_on  = pol_eDon(current_comut_pos_cur_neg)
    
    # For 'D2'
    d2_rec = pol_erec(current_comut_pos_cur_pos)
    d2_on  = pol_eDon(current_comut_neg_cur_pos)
    
    P_sw = {
        'S1': 1/duration * (np.sum(s1_eoff) + np.sum(s1_eon)),
        'S2': 1/duration * (np.sum(s2_eoff) + np.sum(s2_eon)),
        'D1': 1/duration * (np.sum(d1_rec) + np.sum(d1_on)),
        'D2': 1/duration * (np.sum(d2_rec) + np.sum(d2_on))}
    
    if verbate:
        print('# of (positive) Commutations per sec = ', 
              np.sum(commut_pos) / duration)
        print('# of (negative) Commutations per sec = ', 
              np.sum(commut_neg) / duration)
    
    return P_sw


def rmsValue(current):
    '''
    Calculate the RMS value.
    '''
    import numpy as np
    return np.sqrt(np.sum(np.power(current, 2)) / current.size)


def conductionLosesHalfBridge(switch_s1, current, Vce_IGBT, Vf_Diode, Rce_IGBT,
                              Rf_Diode):
    '''
    Table with Conduction Losses for a half-bridge inverter (2-levels).
    
    Parameters
    ----------
    switch_s1: numpy.array
        Is the digital PWM command of the top leg switch of the inverter.   
    current: numpy.array
        Is the current measurment array. Generally is the phase out current of 
        the converter.
    
    Vce_IGBT, Vf_Diode, Rce_IGBT, Rf_Diode: float
        Are the Vout and Rout of each semiconductor of inverter. Considering 
        the same component to the top and bottom switchs.
    '''
    import numpy as np
    
    switch_s1 = np.array(switch_s1)
    current = np.array(current)
    
    switch_s2 = np.zeros(switch_s1.size)
    switch_s2 = switch_s1 == 0
    
    pos_current = current >= 0
    neg_current = current < 0
    s1_times_current = switch_s1 * current
    s2_times_current = switch_s2 * current
    current_s1 = np.zeros(current.size)
    current_s1[pos_current] = s1_times_current[pos_current]
    current_d1 = np.zeros(current.size)
    current_d1[neg_current] = -1 * s1_times_current[neg_current]
    current_s2 = np.zeros(current.size)
    current_s2[neg_current] = -1 * s2_times_current[neg_current]
    current_d2 = np.zeros(current.size)
    current_d2[pos_current] = s2_times_current[pos_current]

    s1_cd = Vce_IGBT  * np.mean(current_s1) + Rce_IGBT  * np.power(rmsValue(current_s1), 2) 
    s2_cd = Vce_IGBT  * np.mean(current_s2) + Rce_IGBT  * np.power(rmsValue(current_s2), 2)
    d1_cd = Vf_Diode * np.mean(current_d1) + Rf_Diode * np.power(rmsValue(current_d1), 2)
    d2_cd = Vf_Diode * np.mean(current_d2) + Rf_Diode * np.power(rmsValue(current_d2), 2)
    
    P_cd = {'S1': s1_cd,
            'S2': s2_cd,
            'D1': d1_cd,
            'D2': d2_cd}
    
    return P_cd
