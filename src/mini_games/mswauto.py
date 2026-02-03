"""
自动化扫雷，高通量进行扫雷游戏并记录结果，以进行理论分析。
"""

from mswlib import MineField, MineFieldAdvisor

def run_minesweeper(rows, cols, mines, seed, first_click):
    mf = MineField(rows, cols, mines, seed=seed, first_click_pos=first_click)
    advisor = MineFieldAdvisor(mf, seed=seed)
    while True:
        if mf.is_safe():
            return True
        if mf.is_dead():
            return False
        advisor.analyze()

        changed = False
        for pos in mf.all_places():
            if advisor.confident_suggestions[pos]==1:
                changed |= mf.dig(pos)
            elif advisor.confident_suggestions[pos]==2:
                changed |= mf.flag(pos)
        
        if changed:
            continue
        
        if (advisor.probability_suggestions>=0).any():
            minimum_possibility = advisor.probability_suggestions[advisor.probability_suggestions>=0].min()
            maximum_possibility = advisor.probability_suggestions[advisor.probability_suggestions>=0].max()
            if minimum_possibility<=1-maximum_possibility:
                positions = [pos for pos in mf.all_places() if advisor.probability_suggestions[pos]==minimum_possibility]
                pos = tuple(mf.rng.choice(positions))
                mf.dig(pos)
            else:
                positions = [pos for pos in mf.all_places() if advisor.probability_suggestions[pos]==maximum_possibility]
                pos = tuple(mf.rng.choice(positions))
                mf.flag(pos)
        else:
            existing_positions = [pos for pos in mf.all_places() if not mf.is_exposed(pos)]
            pos = tuple(mf.rng.choice(existing_positions))
            mf.dig(pos)


def run_simulations(difficulty, start_position, num_simulations, n_workers=1, quiet=False):
    import time
    difficulties = {
        'beginner': (9, 9, 10),
        'intermediate': (16, 16, 40),
        'expert': (16, 30, 99)
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
    parser.add_argument('--difficulty', type=str, required=True, help='Difficulty level: beginner, intermediate, expert')
    parser.add_argument('--start-position', type=str, default='center', help='First click position: center, corner, margin-top, margin-left, quarters')
    parser.add_argument('--simulations', type=int, default=1000, help='Number of simulations to run')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    args = parser.parse_args()
    win_rate = run_simulations(args.difficulty, args.start_position, args.simulations, n_workers=args.workers, quiet=args.quiet)
    print(f"Win rate over {args.simulations} simulations: {win_rate*100:.2f}%")
