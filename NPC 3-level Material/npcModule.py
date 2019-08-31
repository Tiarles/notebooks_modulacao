

def detectCommutation(y, showPlot = False):
    y1 = y[:-1]
    y2 = y[1:]
    
    diff = y2 - y1
    
    if showPlot:
    	plt.subplot(311)
    	plt.plot(y1, label='y1')
    	plt.legend()
    	plt.subplot(312)
	    plt.plot(y2, label='y2')
	    plt.legend()
	    plt.subplot(313)
	    plt.plot(diff, label='diff')
	    plt.legend()
	    plt.show()
    return diff


def switchingLosesNPC(switch_s1, switch_s2, current, duration, 
					  eon1, eoff1, erec1, 
                      eon2, eoff2, erec2):
    '''
        Table with Switching Losses for TDD NPC 3-Levels.
        Curves:
            * eon_params1, eoff_params1 and erec_params1: IGBT1/DIODE5
            * eon_params2, eoff_params2 and erec_params2: IGBT2/DIODE1
        Based in a Semikron Manual, SKiM301MLI12E4
    '''

    switch_s1 = np.array(switch_s1)
    switch_s2 = np.array(switch_s2)
    
    current = np.array(current)
    
    commut1 = detectCommutation(switch_s1)
    commut2 = detectCommutation(switch_s2)
    
    stateA = np.zeros(commut1.size)
    stateB = np.zeros(commut1.size)
    stateC = np.zeros(commut1.size)
    stateD = np.zeros(commut1.size)
    
    stateA[commut1 == 1] = 1
    stateB[commut1 == -1] = 1
    stateC[commut2 == -1] = 1
    stateD[commut2 == 1] = 1
    
    current0 = current[1:]
    
    current_pos = current0 >= 0
    current_neg = current0 < 0
    
    stateA_cur_pos = stateA * current_pos
    stateA_cur_neg = stateA * current_neg
        
    stateB_cur_pos = stateB * current_pos
    stateB_cur_neg = stateB * current_neg
    
    stateC_cur_pos = stateC * current_pos
    stateC_cur_neg = stateC * current_neg
    
    stateD_cur_pos = stateD * current_pos
    stateD_cur_neg = stateD * current_neg

    # For 'S1'
    s1_eon  = eon1(stateA_cur_pos)
    s1_eoff = eoff1(stateB_cur_pos)
    
    # For 'S2'
    s2_eon  = eon2(stateD_cur_pos)
    s2_eoff = eoff2(stateC_cur_pos)
    
    # For 'S3'
    s3_eon  = eon2(stateB_cur_neg)
    s3_eoff = eoff2(stateA_cur_neg)
    
    # For 'S4'
    s4_eon  = eon1(stateC_cur_neg)
    s4_eoff = eoff1(stateD_cur_neg)

    ###
    
    # For 'D1'
    d1_rec = erec2(stateB_cur_neg)
    
    # For 'D4'
    d4_rec = erec2(stateD_cur_pos)
    
    # For 'D5'
    d5_rec = erec1(stateA_cur_pos)
    
    # For 'D6'
    d6_rec = erec1(stateC_cur_neg)
    
    P_sw = {
        'S1': 1/duration * (np.sum(s1_eoff) + np.sum(s1_eon)),
        'S2': 1/duration * (np.sum(s2_eoff) + np.sum(s2_eon)),
        'S3': 1/duration * (np.sum(s3_eoff) + np.sum(s3_eon)),
        'S4': 1/duration * (np.sum(s4_eoff) + np.sum(s4_eon)),
        
        'D1': 1/duration * (np.sum(d1_rec)),
        'D4': 1/duration * (np.sum(d4_rec)),
        
        'D5': 1/duration * (np.sum(d5_rec)),
        'D6': 1/duration * (np.sum(d6_rec))}
    
    return P_sw
