import wave
import struct
import math
import random
import os

SAMPLE_RATE = 22050

def save_wav(filename, samples):
    """Saves a list of floats (range -1.0 to 1.0) as a 16-bit mono WAV file."""
    # Ensure directory exists
    dir_name = os.path.dirname(filename)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
        
    with wave.open(filename, 'w') as wav_file:
        nchannels = 1
        sampwidth = 2  # 16-bit
        nframes = len(samples)
        wav_file.setparams((nchannels, sampwidth, SAMPLE_RATE, nframes, "NONE", "not compressed"))
        
        # Scale to 16-bit integer range
        packed_data = struct.pack(
            f'<{len(samples)}h',
            *(int(max(-32767, min(32767, s * 32767))) for s in samples)
        )
        wav_file.writeframes(packed_data)
    print(f"Generated: {filename} ({len(samples) / SAMPLE_RATE:.2f} seconds)")

def generate_jump():
    duration = 0.12
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    f0 = 350.0
    f1 = 850.0
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Upward linear sweep phase
        phase = 2.0 * math.pi * (f0 * t + (f1 - f0) / (2.0 * duration) * t**2)
        # Linear decay envelope
        env = 1.0 - (i / num_samples)
        val = env * math.sin(phase) * 0.4
        samples.append(val)
        
    return samples

def generate_point():
    duration = 0.25
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    # Note 1: 650 Hz, starts at t=0, decays fast
    f1 = 650.0
    # Note 2: 980 Hz, starts at t=0.07, decays slightly slower
    f2 = 980.0
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        
        # Chime 1
        val1 = 0.0
        if t >= 0:
            env1 = math.exp(-20.0 * t)
            val1 = env1 * math.sin(2.0 * math.pi * f1 * t) * 0.35
            
        # Chime 2
        val2 = 0.0
        if t >= 0.07:
            t2 = t - 0.07
            env2 = math.exp(-12.0 * t2)
            val2 = env2 * math.sin(2.0 * math.pi * f2 * t2) * 0.35
            
        samples[i] = val1 + val2
        
    return samples

def generate_collision():
    duration = 0.4
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    # Noise combined with low rumble
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-8.0 * t)
        
        noise = random.uniform(-1.0, 1.0)
        rumble = math.sin(2.0 * math.pi * 80.0 * t)
        
        # Mix 60% noise, 40% rumble, apply envelope
        val = env * (0.6 * noise + 0.4 * rumble) * 0.5
        samples.append(val)
        
    return samples

def add_bird_chirp(samples, start_time):
    # A single chirp group consists of 2 or 3 quick chirps
    num_chirps = 3
    chirp_duration = 0.05
    chirp_samples = int(chirp_duration * SAMPLE_RATE)
    chirp_gap = 0.03
    gap_samples = int(chirp_gap * SAMPLE_RATE)
    
    start_idx = int(start_time * SAMPLE_RATE)
    
    for j in range(num_chirps):
        offset = start_idx + j * (chirp_samples + gap_samples)
        f0 = 2400.0
        f1 = 3800.0
        
        for i in range(chirp_samples):
            idx = offset + i
            if idx >= len(samples):
                break
                
            t = i / SAMPLE_RATE
            phase = 2.0 * math.pi * (f0 * t + (f1 - f0) / (2.0 * chirp_duration) * t**2)
            # Bell curve envelope for chirp
            env = math.sin(math.pi * (i / chirp_samples))
            val = env * math.sin(phase) * 0.15
            
            # Mix into existing ambient samples
            samples[idx] += val

def generate_powerup_pickup():
    duration = 0.45
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    # Arpeggio frequencies: C5, E5, G5, C6
    freqs = [523.25, 659.25, 783.99, 1046.50]
    offsets = [0.0, 0.08, 0.16, 0.24]
    
    for idx, (f, start_t) in enumerate(zip(freqs, offsets)):
        start_idx = int(start_t * SAMPLE_RATE)
        for i in range(start_idx, num_samples):
            t = (i - start_idx) / SAMPLE_RATE
            env = math.exp(-15.0 * t)
            val = env * math.sin(2.0 * math.pi * f * t) * 0.25
            samples[i] += val
            
    return samples

def generate_shield_break():
    duration = 0.35
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-10.0 * t)
        
        # High pass white noise (or simple noise)
        noise = random.uniform(-1.0, 1.0)
        
        # Descending glass pitch
        f_start = 800.0
        f_end = 200.0
        f = f_start + (f_end - f_start) * (i / num_samples)
        chime = math.sin(2.0 * math.pi * f * t)
        
        # Mix noise (70%) and metallic chime (30%)
        val = env * (0.7 * noise + 0.3 * chime) * 0.45
        samples.append(val)
        
    return samples

def generate_coin_pickup():
    duration = 0.3
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    # Note 1: B5 (987.77 Hz), starts at t=0
    f1 = 987.77
    # Note 2: E6 (1318.51 Hz), starts at t=0.08
    f2 = 1318.51
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        
        # Chime 1
        val1 = 0.0
        if t >= 0:
            env1 = math.exp(-22.0 * t)
            val1 = env1 * math.sin(2.0 * math.pi * f1 * t) * 0.3
            
        # Chime 2
        val2 = 0.0
        if t >= 0.08:
            t2 = t - 0.08
            env2 = math.exp(-15.0 * t2)
            val2 = env2 * math.sin(2.0 * math.pi * f2 * t2) * 0.35
            
        samples[i] = val1 + val2
        
    return samples


# ============================================================
# HELPER: Add a low-frequency kick drum hit (sub-bass, 40-80Hz)
# These sit well below all game SFX which are 350Hz+
# ============================================================
def add_kick(samples, start_time, volume=0.15):
    """Add a punchy sub-bass kick drum at start_time. Freq range 40-80Hz — never conflicts with SFX."""
    kick_dur = 0.08
    kick_samples = int(kick_dur * SAMPLE_RATE)
    start_idx = int(start_time * SAMPLE_RATE)
    for i in range(kick_samples):
        idx = start_idx + i
        if idx >= len(samples):
            break
        t = i / SAMPLE_RATE
        env = math.exp(-35.0 * t)
        freq = 80.0 - 40.0 * (1.0 - math.exp(-50.0 * t))
        val = env * math.sin(2.0 * math.pi * freq * t) * volume
        samples[idx] += val

def add_hihat(samples, start_time, volume=0.04):
    """Add a very quiet hi-hat tick. Uses filtered noise at low volume so it doesn't mask SFX."""
    hat_dur = 0.03
    hat_samples = int(hat_dur * SAMPLE_RATE)
    start_idx = int(start_time * SAMPLE_RATE)
    last = 0.0
    for i in range(hat_samples):
        idx = start_idx + i
        if idx >= len(samples):
            break
        t = i / SAMPLE_RATE
        env = math.exp(-80.0 * t)
        raw = random.uniform(-1.0, 1.0)
        # High-pass feel (but very quiet)
        filt = 0.3 * last + 0.7 * raw
        last = filt
        samples[idx] += filt * env * volume

def add_bass_pulse(samples, start_time, freq=55.0, duration=0.15, volume=0.1):
    """Add a sustained low bass note. Sits in sub-bass range (40-100Hz)."""
    n = int(duration * SAMPLE_RATE)
    start_idx = int(start_time * SAMPLE_RATE)
    for i in range(n):
        idx = start_idx + i
        if idx >= len(samples):
            break
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * i / n)  # smooth bell
        val = env * math.sin(2.0 * math.pi * freq * t) * volume
        samples[idx] += val

def apply_fade(samples):
    """Apply fade in/out to prevent clicks on loop boundaries."""
    fade_len = int(0.2 * SAMPLE_RATE)
    for i in range(fade_len):
        factor = i / fade_len
        samples[i] *= factor
        samples[-1 - i] *= factor


# ============================================================
# NATURE AMBIENT — 3 intensity tiers
# ============================================================
def generate_nature_ambient():
    """Calm nature — wind + bird chirps. The original."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.94 * last_noise + 0.06 * raw_noise
        last_noise = filtered_noise
        wind_mod = 0.45 + 0.25 * math.sin(2.0 * math.pi * 0.18 * t) + 0.15 * math.sin(2.0 * math.pi * 0.08 * t)
        samples[i] = filtered_noise * wind_mod * 0.5
        
    chirp_times = [1.2, 4.5, 7.8]
    for ct in chirp_times:
        add_bird_chirp(samples, ct)

    apply_fade(samples)
    return samples

def generate_nature_ambient_calm():
    """Calm = original nature ambient (alias)."""
    return generate_nature_ambient()

def generate_nature_ambient_mid():
    """Mid intensity — nature wind + subtle heartbeat-like bass pulse every 1s."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.94 * last_noise + 0.06 * raw_noise
        last_noise = filtered_noise
        wind_mod = 0.5 + 0.3 * math.sin(2.0 * math.pi * 0.22 * t) + 0.15 * math.sin(2.0 * math.pi * 0.1 * t)
        samples[i] = filtered_noise * wind_mod * 0.45
    
    chirp_times = [1.2, 4.5, 7.8]
    for ct in chirp_times:
        add_bird_chirp(samples, ct)
    
    # Add subtle low kick every 1.0s (like a heartbeat — 60BPM)
    for beat_t in [i * 1.0 for i in range(10)]:
        add_kick(samples, beat_t, volume=0.08)
    
    apply_fade(samples)
    return samples

def generate_nature_ambient_intense():
    """Intense — faster wind + rapid low bass drum (120BPM) + tension bass drone."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.93 * last_noise + 0.07 * raw_noise
        last_noise = filtered_noise
        wind_mod = 0.6 + 0.35 * math.sin(2.0 * math.pi * 0.3 * t) + 0.2 * math.sin(2.0 * math.pi * 0.15 * t)
        samples[i] = filtered_noise * wind_mod * 0.4
    
    # Fast kick drum (120 BPM = every 0.5s)
    for beat_t in [i * 0.5 for i in range(20)]:
        add_kick(samples, beat_t, volume=0.12)
        add_hihat(samples, beat_t + 0.25, volume=0.03)
    
    # Low tension drone (sub-bass pad at 45Hz)
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        drone = math.sin(2.0 * math.pi * 45.0 * t) * 0.06
        drone += math.sin(2.0 * math.pi * 67.5 * t) * 0.03  # fifth harmonic hint
        samples[i] += drone
    
    apply_fade(samples)
    return samples


# ============================================================
# SYNTHWAVE AMBIENT — 3 intensity tiers
# ============================================================
def generate_synthwave_ambient():
    """Original synthwave ambient with retro chords and bass beat."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    chords = [
        [110.0, 220.0, 261.63, 329.63],
        [87.31, 174.61, 220.0, 261.63],
        [130.81, 261.63, 329.63, 392.00],
        [98.00, 196.00, 246.94, 293.66]
    ]
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        chord_idx = int((t % 10.0) / 2.5) % len(chords)
        active_chord = chords[chord_idx]
        
        val = 0.0
        for freq in active_chord:
            cycle = t * freq
            tri = 2.0 * abs(2.0 * (cycle - math.floor(cycle + 0.5))) - 1.0
            sine = math.sin(2.0 * math.pi * freq * t)
            lfo = 0.6 + 0.4 * math.sin(2.0 * math.pi * 0.4 * t)
            val += (0.6 * tri + 0.4 * sine) * lfo * 0.1
            
        beat_t = t % 0.625
        bass_env = math.exp(-15.0 * beat_t)
        bass_freq = 60.0 - 40.0 * (1.0 - math.exp(-30.0 * beat_t))
        bass_drum = bass_env * math.sin(2.0 * math.pi * bass_freq * beat_t) * 0.25
        
        samples[i] = (val + bass_drum) * 0.35
        
    apply_fade(samples)
    return samples

def generate_synthwave_ambient_calm():
    return generate_synthwave_ambient()

def generate_synthwave_ambient_mid():
    """Mid — original synth chords + added offbeat hi-hats + slightly louder bass."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    chords = [
        [110.0, 220.0, 261.63, 329.63],
        [87.31, 174.61, 220.0, 261.63],
        [130.81, 261.63, 329.63, 392.00],
        [98.00, 196.00, 246.94, 293.66]
    ]
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        chord_idx = int((t % 10.0) / 2.5) % len(chords)
        active_chord = chords[chord_idx]
        
        val = 0.0
        for freq in active_chord:
            cycle = t * freq
            tri = 2.0 * abs(2.0 * (cycle - math.floor(cycle + 0.5))) - 1.0
            sine = math.sin(2.0 * math.pi * freq * t)
            lfo = 0.6 + 0.4 * math.sin(2.0 * math.pi * 0.5 * t)
            val += (0.6 * tri + 0.4 * sine) * lfo * 0.1
        
        # Louder bass beat at 0.5s intervals (120BPM)
        beat_t_val = t % 0.5
        bass_env = math.exp(-18.0 * beat_t_val)
        bass_freq = 65.0 - 40.0 * (1.0 - math.exp(-35.0 * beat_t_val))
        bass_drum = bass_env * math.sin(2.0 * math.pi * bass_freq * beat_t_val) * 0.3
        
        samples[i] = (val + bass_drum) * 0.38

    # Offbeat hi-hats
    for beat_t in [i * 0.5 + 0.25 for i in range(20)]:
        add_hihat(samples, beat_t, volume=0.035)
    
    apply_fade(samples)
    return samples

def generate_synthwave_ambient_intense():
    """Intense — driving 140BPM beat, heavier bass, faster LFO, punchier drums."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    chords = [
        [110.0, 220.0, 261.63, 329.63],
        [87.31, 174.61, 220.0, 261.63],
        [130.81, 261.63, 329.63, 392.00],
        [98.00, 196.00, 246.94, 293.66]
    ]
    
    bpm_interval = 60.0 / 140.0  # ~0.4286s per beat
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        chord_idx = int((t % 10.0) / 2.5) % len(chords)
        active_chord = chords[chord_idx]
        
        val = 0.0
        for freq in active_chord:
            cycle = t * freq
            tri = 2.0 * abs(2.0 * (cycle - math.floor(cycle + 0.5))) - 1.0
            sine = math.sin(2.0 * math.pi * freq * t)
            # Faster LFO for more urgency
            lfo = 0.5 + 0.5 * math.sin(2.0 * math.pi * 0.7 * t)
            val += (0.55 * tri + 0.45 * sine) * lfo * 0.11
        
        # Punchy 140BPM kick
        beat_t_val = t % bpm_interval
        bass_env = math.exp(-22.0 * beat_t_val)
        bass_freq = 70.0 - 45.0 * (1.0 - math.exp(-40.0 * beat_t_val))
        bass_drum = bass_env * math.sin(2.0 * math.pi * bass_freq * beat_t_val) * 0.35
        
        samples[i] = (val + bass_drum) * 0.4
    
    # Hi-hats on every offbeat
    num_beats = int(duration / bpm_interval)
    for b in range(num_beats):
        add_hihat(samples, b * bpm_interval + bpm_interval * 0.5, volume=0.04)
    
    # Sub-bass drone for tension
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        samples[i] += math.sin(2.0 * math.pi * 55.0 * t) * 0.04
    
    apply_fade(samples)
    return samples


# ============================================================
# CITY AMBIENT — 3 intensity tiers
# ============================================================
def generate_city_ambient():
    """Original city ambient — traffic rumble + distant horns."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    horns = [
        (1.5, 480.0, 0.4, 0.08),
        (1.65, 480.0, 0.35, 0.07),
        (4.2, 350.0, 0.8, 0.06),
        (7.5, 520.0, 0.5, 0.05)
    ]
    
    last_noise = 0.0
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.98 * last_noise + 0.02 * raw_noise
        last_noise = filtered_noise
        
        traffic_wave = 0.5 + 0.3 * math.sin(2.0 * math.pi * 0.11 * t)
        rumble = filtered_noise * traffic_wave * 0.75
        
        horn_mix = 0.0
        for start_t, freq, dur, vol in horns:
            if start_t <= t < start_t + dur:
                ht = t - start_t
                env = math.sin(math.pi * (ht / dur))
                horn_mix += env * math.sin(2.0 * math.pi * freq * ht) * vol
                
        samples[i] = (rumble + horn_mix) * 0.4
        
    apply_fade(samples)
    return samples

def generate_city_ambient_calm():
    return generate_city_ambient()

def generate_city_ambient_mid():
    """Mid — city rumble + a slow industrial beat (80BPM kick)."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    horns = [
        (1.5, 480.0, 0.4, 0.08),
        (4.2, 350.0, 0.8, 0.06),
        (7.5, 520.0, 0.5, 0.05)
    ]
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.98 * last_noise + 0.02 * raw_noise
        last_noise = filtered_noise
        
        traffic_wave = 0.55 + 0.35 * math.sin(2.0 * math.pi * 0.13 * t)
        rumble = filtered_noise * traffic_wave * 0.7
        
        horn_mix = 0.0
        for start_t, freq, dur, vol in horns:
            if start_t <= t < start_t + dur:
                ht = t - start_t
                env = math.sin(math.pi * (ht / dur))
                horn_mix += env * math.sin(2.0 * math.pi * freq * ht) * vol
                
        samples[i] = (rumble + horn_mix) * 0.4
    
    # Industrial kick at 80BPM (every 0.75s)
    for beat_t in [i * 0.75 for i in range(14)]:
        add_kick(samples, beat_t, volume=0.1)
    
    apply_fade(samples)
    return samples

def generate_city_ambient_intense():
    """Intense — heavier traffic, fast industrial beat (130BPM), metallic percussion."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    horns = [
        (1.0, 480.0, 0.3, 0.09),
        (2.5, 400.0, 0.5, 0.07),
        (5.0, 350.0, 0.6, 0.08),
        (7.0, 520.0, 0.4, 0.06),
        (8.5, 460.0, 0.35, 0.07)
    ]
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.97 * last_noise + 0.03 * raw_noise
        last_noise = filtered_noise
        
        traffic_wave = 0.6 + 0.35 * math.sin(2.0 * math.pi * 0.18 * t)
        rumble = filtered_noise * traffic_wave * 0.65
        
        horn_mix = 0.0
        for start_t, freq, dur, vol in horns:
            if start_t <= t < start_t + dur:
                ht = t - start_t
                env = math.sin(math.pi * (ht / dur))
                horn_mix += env * math.sin(2.0 * math.pi * freq * ht) * vol
                
        samples[i] = (rumble + horn_mix) * 0.42
    
    bpm_interval = 60.0 / 130.0
    num_beats = int(duration / bpm_interval)
    for b in range(num_beats):
        add_kick(samples, b * bpm_interval, volume=0.13)
        add_hihat(samples, b * bpm_interval + bpm_interval * 0.5, volume=0.04)
    
    # Low industrial hum
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        samples[i] += math.sin(2.0 * math.pi * 50.0 * t) * 0.04
    
    apply_fade(samples)
    return samples


# ============================================================
# WINTER AMBIENT — 3 intensity tiers
# ============================================================
def generate_winter_ambient():
    """Original winter ambient — howling wind + whistling gusts."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    last_noise = 0.0
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.94 * last_noise + 0.06 * raw_noise
        last_noise = filtered_noise
        
        gale_mod = 0.5 + 0.3 * math.sin(2.0 * math.pi * 0.15 * t) + 0.2 * math.cos(2.0 * math.pi * 0.07 * t)
        base_gale = filtered_noise * gale_mod * 0.5
        
        f1 = 450.0 + 150.0 * math.sin(2.0 * math.pi * 0.12 * t)
        f2 = 800.0 + 200.0 * math.cos(2.0 * math.pi * 0.18 * t)
        
        whistle_mod1 = max(0.0, 0.3 + 0.7 * math.sin(2.0 * math.pi * 0.2 * t)) * abs(raw_noise)
        whistle_mod2 = max(0.0, 0.2 + 0.8 * math.cos(2.0 * math.pi * 0.25 * t)) * abs(raw_noise)
        
        whistle1 = math.sin(2.0 * math.pi * f1 * t) * whistle_mod1 * 0.18
        whistle2 = math.sin(2.0 * math.pi * f2 * t) * whistle_mod2 * 0.12
        
        samples[i] = (base_gale + whistle1 + whistle2) * 0.35
        
    apply_fade(samples)
    return samples

def generate_winter_ambient_calm():
    return generate_winter_ambient()

def generate_winter_ambient_mid():
    """Mid — winter wind + slow deep heartbeat pulse."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.94 * last_noise + 0.06 * raw_noise
        last_noise = filtered_noise
        
        gale_mod = 0.55 + 0.3 * math.sin(2.0 * math.pi * 0.18 * t) + 0.2 * math.cos(2.0 * math.pi * 0.09 * t)
        base_gale = filtered_noise * gale_mod * 0.45
        
        f1 = 450.0 + 180.0 * math.sin(2.0 * math.pi * 0.14 * t)
        whistle_mod1 = max(0.0, 0.3 + 0.7 * math.sin(2.0 * math.pi * 0.22 * t)) * abs(raw_noise)
        whistle1 = math.sin(2.0 * math.pi * f1 * t) * whistle_mod1 * 0.15
        
        samples[i] = (base_gale + whistle1) * 0.35
    
    # Heartbeat-like double kick (lub-dub) every 1.2s
    for b in range(8):
        add_kick(samples, b * 1.2, volume=0.09)
        add_kick(samples, b * 1.2 + 0.18, volume=0.06)
    
    apply_fade(samples)
    return samples

def generate_winter_ambient_intense():
    """Intense — blizzard wind + fast tense drums (130BPM) + icy sub-bass."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.93 * last_noise + 0.07 * raw_noise
        last_noise = filtered_noise
        
        gale_mod = 0.6 + 0.35 * math.sin(2.0 * math.pi * 0.25 * t) + 0.25 * math.cos(2.0 * math.pi * 0.12 * t)
        base_gale = filtered_noise * gale_mod * 0.4
        
        f1 = 500.0 + 200.0 * math.sin(2.0 * math.pi * 0.2 * t)
        f2 = 850.0 + 250.0 * math.cos(2.0 * math.pi * 0.28 * t)
        whistle_mod1 = max(0.0, 0.4 + 0.6 * math.sin(2.0 * math.pi * 0.3 * t)) * abs(raw_noise)
        whistle_mod2 = max(0.0, 0.3 + 0.7 * math.cos(2.0 * math.pi * 0.35 * t)) * abs(raw_noise)
        whistle1 = math.sin(2.0 * math.pi * f1 * t) * whistle_mod1 * 0.12
        whistle2 = math.sin(2.0 * math.pi * f2 * t) * whistle_mod2 * 0.08
        
        samples[i] = (base_gale + whistle1 + whistle2) * 0.35
    
    bpm_interval = 60.0 / 130.0
    num_beats = int(duration / bpm_interval)
    for b in range(num_beats):
        add_kick(samples, b * bpm_interval, volume=0.12)
        add_hihat(samples, b * bpm_interval + bpm_interval * 0.5, volume=0.03)
    
    # Icy sub-bass drone
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        samples[i] += math.sin(2.0 * math.pi * 42.0 * t) * 0.05
    
    apply_fade(samples)
    return samples


# ============================================================
# RAIN AMBIENT — 3 intensity tiers
# ============================================================
def generate_rain_ambient():
    """Original rain ambient — rain sheets + thunder rumbles."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    thunder = [
        (2.0, 4.5, 0.45),
        (7.5, 2.5, 0.3)
    ]
    
    last_noise = 0.0
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.992 * last_noise + 0.008 * raw_noise
        last_noise = filtered_noise
        
        thunder_mix = 0.0
        for start_t, dur, vol in thunder:
            if start_t <= t < start_t + dur:
                tt = t - start_t
                if tt < 1.0:
                    env = math.sin(math.pi * 0.5 * tt)
                else:
                    env = math.exp(-1.5 * (tt - 1.0))
                crackle = 0.8 + 0.2 * random.uniform(-1.0, 1.0)
                thunder_mix += filtered_noise * env * crackle * vol * 5.0
                
        rain_sheet = raw_noise * 0.06
        
        drop_crackle = 0.0
        if random.random() < 0.003:
            drop_crackle = random.choice([-1.0, 1.0]) * random.uniform(0.1, 0.25)
            
        samples[i] = (thunder_mix + rain_sheet + drop_crackle) * 0.45
        
    apply_fade(samples)
    return samples

def generate_rain_ambient_calm():
    return generate_rain_ambient()

def generate_rain_ambient_mid():
    """Mid — heavier rain + a slow ominous bass pulse."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    thunder = [
        (1.5, 3.5, 0.4),
        (6.0, 3.0, 0.35),
        (8.5, 2.0, 0.25)
    ]
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.992 * last_noise + 0.008 * raw_noise
        last_noise = filtered_noise
        
        thunder_mix = 0.0
        for start_t, dur, vol in thunder:
            if start_t <= t < start_t + dur:
                tt = t - start_t
                if tt < 1.0:
                    env = math.sin(math.pi * 0.5 * tt)
                else:
                    env = math.exp(-1.5 * (tt - 1.0))
                crackle = 0.8 + 0.2 * random.uniform(-1.0, 1.0)
                thunder_mix += filtered_noise * env * crackle * vol * 5.0
        
        rain_sheet = raw_noise * 0.08  # heavier rain
        
        drop_crackle = 0.0
        if random.random() < 0.005:
            drop_crackle = random.choice([-1.0, 1.0]) * random.uniform(0.1, 0.3)
            
        samples[i] = (thunder_mix + rain_sheet + drop_crackle) * 0.42
    
    # Slow ominous bass pulse every 1.5s
    for beat_t in [i * 1.5 for i in range(7)]:
        add_bass_pulse(samples, beat_t, freq=50.0, duration=0.3, volume=0.08)
    
    apply_fade(samples)
    return samples

def generate_rain_ambient_intense():
    """Intense — storm fury, constant heavy rain, rapid drums, deep rumble drone."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    thunder = [
        (0.5, 3.0, 0.5),
        (4.0, 4.0, 0.45),
        (8.0, 2.5, 0.35)
    ]
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.991 * last_noise + 0.009 * raw_noise
        last_noise = filtered_noise
        
        thunder_mix = 0.0
        for start_t, dur, vol in thunder:
            if start_t <= t < start_t + dur:
                tt = t - start_t
                if tt < 0.8:
                    env = math.sin(math.pi * 0.5 * (tt / 0.8))
                else:
                    env = math.exp(-1.2 * (tt - 0.8))
                crackle = 0.75 + 0.25 * random.uniform(-1.0, 1.0)
                thunder_mix += filtered_noise * env * crackle * vol * 5.5
        
        rain_sheet = raw_noise * 0.1  # heavy rain
        
        drop_crackle = 0.0
        if random.random() < 0.008:
            drop_crackle = random.choice([-1.0, 1.0]) * random.uniform(0.15, 0.35)
            
        samples[i] = (thunder_mix + rain_sheet + drop_crackle) * 0.4
    
    # Fast kick (120BPM)
    for beat_t in [i * 0.5 for i in range(20)]:
        add_kick(samples, beat_t, volume=0.1)
    
    # Deep rumble drone
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        samples[i] += math.sin(2.0 * math.pi * 38.0 * t) * 0.05
    
    apply_fade(samples)
    return samples


# ============================================================
# SNOWFALL AMBIENT (bonus)
# ============================================================
def generate_snowfall_ambient():
    """Gentle snowfall — very soft wind + crystalline chimes."""
    duration = 10.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    last_noise = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        raw_noise = random.uniform(-1.0, 1.0)
        filtered_noise = 0.96 * last_noise + 0.04 * raw_noise
        last_noise = filtered_noise
        gale_mod = 0.3 + 0.2 * math.sin(2.0 * math.pi * 0.1 * t)
        samples[i] = filtered_noise * gale_mod * 0.3
    
    apply_fade(samples)
    return samples


def main():
    print("Generating game sounds...")
    
    # Create sounds directory if not existing
    os.makedirs("assets/sounds", exist_ok=True)
    
    # Core SFX
    save_wav("assets/sounds/jump.wav", generate_jump())
    save_wav("assets/sounds/point.wav", generate_point())
    save_wav("assets/sounds/collision.wav", generate_collision())
    save_wav("assets/sounds/powerup_pickup.wav", generate_powerup_pickup())
    save_wav("assets/sounds/shield_break.wav", generate_shield_break())
    save_wav("assets/sounds/coin_pickup.wav", generate_coin_pickup())
    
    # Nature ambient (3 tiers + original)
    save_wav("assets/sounds/nature_ambient.wav", generate_nature_ambient())
    save_wav("assets/sounds/nature_ambient_calm.wav", generate_nature_ambient_calm())
    save_wav("assets/sounds/nature_ambient_mid.wav", generate_nature_ambient_mid())
    save_wav("assets/sounds/nature_ambient_intense.wav", generate_nature_ambient_intense())
    
    # Synthwave ambient (3 tiers + original)
    save_wav("assets/sounds/synthwave_ambient.wav", generate_synthwave_ambient())
    save_wav("assets/sounds/synthwave_ambient_calm.wav", generate_synthwave_ambient_calm())
    save_wav("assets/sounds/synthwave_ambient_mid.wav", generate_synthwave_ambient_mid())
    save_wav("assets/sounds/synthwave_ambient_intense.wav", generate_synthwave_ambient_intense())
    
    # City ambient (3 tiers + original)
    save_wav("assets/sounds/city_ambient.wav", generate_city_ambient())
    save_wav("assets/sounds/city_ambient_calm.wav", generate_city_ambient_calm())
    save_wav("assets/sounds/city_ambient_mid.wav", generate_city_ambient_mid())
    save_wav("assets/sounds/city_ambient_intense.wav", generate_city_ambient_intense())
    
    # Winter ambient (3 tiers + original)
    save_wav("assets/sounds/winter_ambient.wav", generate_winter_ambient())
    save_wav("assets/sounds/winter_ambient_calm.wav", generate_winter_ambient_calm())
    save_wav("assets/sounds/winter_ambient_mid.wav", generate_winter_ambient_mid())
    save_wav("assets/sounds/winter_ambient_intense.wav", generate_winter_ambient_intense())
    
    # Rain ambient (3 tiers + original)
    save_wav("assets/sounds/rain_ambient.wav", generate_rain_ambient())
    save_wav("assets/sounds/rain_ambient_calm.wav", generate_rain_ambient_calm())
    save_wav("assets/sounds/rain_ambient_mid.wav", generate_rain_ambient_mid())
    save_wav("assets/sounds/rain_ambient_intense.wav", generate_rain_ambient_intense())
    
    # Bonus: Snowfall ambient
    save_wav("assets/sounds/snowfall_ambient.wav", generate_snowfall_ambient())
    
    print("All sounds generated successfully!")
    convert_to_ogg()

def convert_to_ogg():
    print("Post-processing: Converting WAV files to OGG...")
    import subprocess
    
    # Try to add static_ffmpeg path if package is installed
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except ImportError:
        pass
        
    sounds_dir = "assets/sounds"
    if not os.path.exists(sounds_dir):
        return
        
    converted = 0
    errors = 0
    for f in os.listdir(sounds_dir):
        if f.endswith(".wav"):
            wav_path = os.path.join(sounds_dir, f)
            ogg_path = os.path.join(sounds_dir, f.replace(".wav", ".ogg"))
            
            try:
                # Run ffmpeg command
                res = subprocess.run(
                    ["ffmpeg", "-y", "-i", wav_path, "-c:a", "libvorbis", "-q:a", "4", ogg_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if res.returncode == 0:
                    os.remove(wav_path)
                    converted += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                
    if converted > 0:
        print(f"Successfully converted {converted} WAV files to OGG and cleaned up temporary WAVs.")
    if errors > 0:
        print("Note: Some files could not be converted (make sure ffmpeg is on system path or static-ffmpeg is installed).")

if __name__ == "__main__":
    main()
