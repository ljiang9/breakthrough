"""突破棋 (Breakthrough)：8x8 棋盘，每方 16 个兵，只能向前走或向前斜吃子，
第一个到达对方底线者获胜。纯标准库。"""
from __future__ import annotations

import argparse
import copy
import random
import sys

ROWS, COLS = 8, 8
BLACK, WHITE = 0, 1  # 黑方从上往下(+1)，白方从下往上(-1)
SYMBOLS = {BLACK: "●", WHITE: "○"}


def new_board() -> list[list[int | None]]:
    """初始局面：黑方在第 0-1 行，白方在第 6-7 行。"""
    b = [[None] * COLS for _ in range(ROWS)]
    for r in (0, 1):
        b[r] = [BLACK] * COLS
    for r in (6, 7):
        b[r] = [WHITE] * COLS
    return b


def legal_moves(board, player) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """返回 [(from, to)]。规则：向前走一格（必须空）；向前斜一格只能吃子。"""
    d = 1 if player == BLACK else -1
    foe = WHITE if player == BLACK else BLACK
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != player:
                continue
            fr = r + d
            if not (0 <= fr < ROWS):
                continue
            if board[fr][c] is None:
                moves.append(((r, c), (fr, c)))
            for dc in (-1, 1):
                fc = c + dc
                if 0 <= fc < COLS and board[fr][fc] == foe:
                    moves.append(((r, c), (fr, fc)))
    return moves


def apply_move(board, move):
    """执行走法，返回新棋盘。非法走法抛 ValueError。"""
    (r, c), (tr, tc) = move
    piece = board[r][c]
    if piece not in (BLACK, WHITE):
        raise ValueError(f"起点没有棋子: {move}")
    legal = legal_moves(board, piece)
    if move not in legal:
        raise ValueError(f"非法走法: {move}")
    nb = copy.deepcopy(board)
    nb[tr][tc] = piece
    nb[r][c] = None
    return nb


def winner(board) -> int | None:
    """BLACK 先到第 7 行胜，WHITE 先到第 0 行胜。"""
    for c in range(COLS):
        if board[ROWS - 1][c] == BLACK:
            return BLACK
        if board[0][c] == WHITE:
            return WHITE
    return None


def is_over(board) -> bool:
    return winner(board) is not None


def render(board) -> str:
    lines = ["  " + " ".join(str(c) for c in range(COLS))]
    for r in range(ROWS):
        row = " ".join(SYMBOLS.get(board[r][c], "·") for c in range(COLS))
        lines.append(f"{r} {row}")
    return "\n".join(lines)


def evaluate(board, player) -> float:
    """贪心评估：子力 + 推进进度（按方向）+ 吃子威胁。"""
    d = 1 if player == BLACK else -1
    foe = WHITE if player == BLACK else BLACK
    score = 0.0
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r][c]
            if p is None:
                continue
            progress = (r if d == 1 else (ROWS - 1 - r)) / (ROWS - 1)
            val = 10.0 + 6.0 * progress
            # 临门一脚加成
            if p == BLACK and r == ROWS - 2:
                val += 4.0
            if p == WHITE and r == 1:
                val += 4.0
            score += val if p == player else -val
            # 被吃威胁惩罚
            fr = r + (1 if p == BLACK else -1)
            if 0 <= fr < ROWS:
                for dc in (-1, 1):
                    fc = c + dc
                    if 0 <= fc < COLS and board[fr][fc] == (foe if p == player else player):
                        score += -1.5 if p == player else 1.5
    return score


def ai_move(board, player, rng) -> tuple | None:
    moves = legal_moves(board, player)
    if not moves:
        return None
    scored = []
    for mv in moves:
        nb = apply_move(board, mv)
        w = winner(nb)
        if w == player:
            return mv  # 直接获胜
        scored.append((evaluate(nb, player) + rng.random() * 0.01, mv))
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


def play_auto(games=10, seed=42, verbose=False):
    rng = random.Random(seed)
    results = {BLACK: 0, WHITE: 0, "draw": 0}
    for g in range(games):
        board = new_board()
        player = BLACK
        plies = 0
        while not is_over(board) and plies < 400:
            mv = ai_move(board, player, rng)
            if mv is None:
                results["draw"] += 1
                break
            board = apply_move(board, mv)
            plies += 1
            player = WHITE if player == BLACK else BLACK
        else:
            w = winner(board)
            if w is not None:
                results[w] += 1
            else:
                results["draw"] += 1
        if verbose:
            w = winner(board)
            name = {BLACK: "黑", WHITE: "白"}.get(w, "和棋")
            suffix = "胜" if w is not None else ""
            print(f"第 {g+1}/{games} 局：{name}{suffix}，{plies} 手")
    b, w_, d = results[BLACK], results[WHITE], results["draw"]
    print(f"总计：黑胜 {b}，白胜 {w_}，和棋 {d}")
    return results


def parse_coord(s: str) -> tuple[int, int]:
    r, c = s.split(",")
    return int(r.strip()), int(c.strip())


def play_interactive():
    board = new_board()
    player = BLACK
    names = {BLACK: "黑方(●)", WHITE: "白方(○)"}
    while not is_over(board):
        print(render(board))
        moves = legal_moves(board, player)
        if not moves:
            print(f"{names[player]} 无子可走，和棋。")
            return
        print(f"{names[player]} 行棋，格式如 1,3-2,3（起点-终点），q 退出")
        try:
            s = input("> ").strip()
        except EOFError:
            return
        if s.lower() == "q":
            return
        try:
            a, b_ = s.split("-")
            mv = (parse_coord(a), parse_coord(b_))
            board = apply_move(board, mv)
        except (ValueError, IndexError) as e:
            print(f"非法走法：{e}")
            continue
        player = WHITE if player == BLACK else BLACK
    print(render(board))
    print(f"{names[winner(board)]} 获胜！")


def main(argv=None):
    ap = argparse.ArgumentParser(description="突破棋 (Breakthrough)：先到对方底线者胜")
    ap.add_argument("--auto", action="store_true", help="AI 对 AI 自动演示")
    ap.add_argument("--games", type=int, default=10, help="自动演示局数")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--verbose", action="store_true", help="自动演示打印每局")
    args = ap.parse_args(argv)
    if args.auto:
        play_auto(games=args.games, seed=args.seed, verbose=args.verbose)
    else:
        if not sys.stdin.isatty():
            print("交互模式需要终端；无头演示请用 --auto", file=sys.stderr)
            sys.exit(2)
        play_interactive()


if __name__ == "__main__":
    main()
