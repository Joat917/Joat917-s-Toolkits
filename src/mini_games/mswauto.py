"""
自动化扫雷，高通量进行扫雷游戏并记录结果，以进行理论分析。
"""

from mswlib2 import MineGame, MineDetector

def run_minesweeper(rows, cols, mines, seed, first_click):
    game = MineGame(rows, cols, mines, seed=seed)
    if first_click is not None:
        game.reveal_cell(first_click)
    field = game.minefield
    detector = MineDetector(field)
    _reset_loop_left = 5
    while True:
        if field.is_victory():
            return True
        if not field.is_safe():
            return False

        try:
            detector.refresh()
        except Exception as e:
            print(f"Error in detector.refresh(): {e}")
            detector = MineDetector(field)
            detector.reset()
            detector.refresh()

        to_dig = []
        to_flag = []
        for pos in field.all_indices():
            if (detector.known_mines[pos] or detector.probabilities[pos] == 1.0) and not field.is_flag(pos):
                to_flag.append(pos)
            if detector.known_empty[pos] or detector.probabilities[pos] == 0.0 and not field.is_exposed(pos):
                to_dig.append(pos)
            

        changed = False
        for pos in to_flag:
            if not field.is_flag(pos):
                changed |= game.mark_cell(pos)!=0
        for pos in to_dig:
            if not field.is_exposed(pos):
                changed |= game.reveal_cell(pos)!=0
        
        if changed:
            continue
        
        all_next_possible_step = []
        for cell in field.all_indices():
            if field.is_covered(cell) and not detector.known_mines[cell]:
                all_next_possible_step.append(cell)

        if len(all_next_possible_step)>0:
            from random import shuffle
            shuffle(all_next_possible_step)
            all_next_possible_step.sort(key=lambda pos: detector.probabilities[pos])
            for cell in all_next_possible_step:
                changed += abs(game.reveal_cell(cell))
                if changed>0:
                    break

        if not changed:
            _reset_loop_left -= 1
            if _reset_loop_left <= 0:
                return False
            detector.reset()
            detector.refresh()


def run_simulations(difficulty, start_position, num_simulations, n_workers=1, quiet=False):
    import time
    difficulties = {
        'beginner': (9, 9, 10),
        'intermediate': (16, 16, 40),
        'expert': (16, 30, 99), 
        'extreme': (64, 36, 999)
    }
    positions = {
        'center': lambda r, c: (r//2, c//2),
        'corner': lambda r, c: (0, 0),
        'margin-top': lambda r, c: (0, c//2), 
        'margin-left': lambda r, c: (r//2, 0),
        'quarters': lambda r, c: (r//4, c//4)
    }
    if difficulty in difficulties:
        rows, cols, mines = difficulties[difficulty]
    else:
        raise ValueError("Unknown difficulty level.")
    if start_position in positions:
        first_click = positions[start_position](rows, cols)
    else:
        raise ValueError("Unknown start position.")
    
    if not quiet:
        import tqdm
        pbar = tqdm.tqdm(total=num_simulations, desc="Simulating Minesweeper")
        def update(*args): pbar.update(1)
    else:
        def update(*args): pass
    if n_workers == 1:
        results = []
        for seed in range(num_simulations):
            result = run_minesweeper(rows, cols, mines, seed, first_click)
            results.append(result)
            update()
        return sum(results)/num_simulations
    else:
        from multiprocessing import Pool
        with Pool(n_workers) as pool:
            args = [(rows, cols, mines, seed, first_click) for seed in range(num_simulations)]
            tasks = [pool.apply_async(run_minesweeper, arg, callback=update) for arg in args]
            results = [task.get() for task in tasks]
        return sum(results)/num_simulations

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Automated Minesweeper Simulator")
    parser.add_argument('--difficulty', type=str, required=True, help='Difficulty level: beginner, intermediate, expert, extreme')
    parser.add_argument('--start-position', type=str, default='center', help='First click position: center, corner, margin-top, margin-left, quarters')
    parser.add_argument('--simulations', type=int, default=1000, help='Number of simulations to run')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    args = parser.parse_args()
    win_rate = run_simulations(args.difficulty, args.start_position, args.simulations, n_workers=args.workers, quiet=args.quiet)
    print(f"Win rate over {args.simulations} simulations: {win_rate*100:.2f}%")
