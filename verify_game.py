import os
import sys
import random
sys.path.insert(0, r"c:\Users\saisa\OneDrive\Desktop\game")

# Set dummy drivers for headless pygame testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# Import pygame and initialize
import pygame
pygame.init()
pygame.mixer.init()

# Import the Game class
try:
    from main import Game, WIDTH, HEIGHT
    print("Successfully imported game module.")
except Exception as e:
    print(f"Error importing game: {e}")
    sys.exit(1)

def run_test():
    try:
        # Initialize Game
        print("Initializing Game...")
        game = Game()
        
        # Test default mode (Forest) ambient track
        track = game.get_ambient_track()
        print(f"Initial mode: {game.mode}, initial ambient track: {track}")
        assert track == "nature_ambient_calm", f"Expected nature_ambient_calm, got {track}"
        
        # Test dynamic climate weather transitions
        print("Starting game in normal mode...")
        game.mode = "normal"
        game.start_game()
        print(f"Post start_game: is_raining={game.is_raining}, is_windy={game.is_windy}")
        assert game.is_raining is False, "Expected game to start clear"
        assert len(game.rain_particles) == 45, f"Expected 45 pre-populated rain particles, got {len(game.rain_particles)}"
        assert len(game.wind_particles) == 15, f"Expected 15 pre-populated wind particles, got {len(game.wind_particles)}"
        
        # Fast-forward to Rainy phase (sky_ticks = 1200)
        game.sky_ticks = 1200
        game.update()
        print(f"Rainy phase: is_raining={game.is_raining}, is_windy={game.is_windy}, track={game.get_ambient_track()}")
        assert game.is_raining is True, "Expected is_raining to be True in phase 2"
        assert game.get_ambient_track().startswith("rain_ambient"), "Expected rain ambient track"
        
        # Fast-forward to Windy phase (sky_ticks = 1800)
        game.sky_ticks = 1800
        game.update()
        print(f"Windy phase: is_raining={game.is_raining}, is_windy={game.is_windy}, track={game.get_ambient_track()}")
        assert game.is_windy is True, "Expected is_windy to be True in phase 3"
        assert game.get_ambient_track().startswith("winter_ambient"), "Expected winter/wind ambient track"
        
        # Update and draw loop simulation (120 ticks/frames)
        print("Running 120 ticks of update and draw...")
        surface = pygame.Surface((WIDTH, HEIGHT))
        for tick in range(120):
            game.update()
            game.draw()
            
            # Periodically force a lightning flash
            if tick == 60:
                print("Simulating lightning trigger...")
                game.lightning_flash_timer = 2
                
        print("No runtime exceptions occurred during headless simulation!")
        
        # Test mode switching audio tracks
        game.sky_ticks = 0
        game.sky_phase = 0
        game.is_windy = False
        game.is_raining = False
        modes = ["normal", "night", "city", "winter"]
        expected_tracks = ["nature_ambient_calm", "synthwave_ambient_calm", "city_ambient_calm", "winter_ambient_calm"]
        for m, t in zip(modes, expected_tracks):
            game.mode = m
            game.is_raining = False
            game.is_windy = False
            track = game.get_ambient_track()
            print(f"Mode: {m} -> Track: {track}")
            assert track == t, f"Expected {t} for mode {m}, got {track}"
            
        print("All assertions passed successfully!")
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_test()
