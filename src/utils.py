from tqdm import tqdm

def create_progress(total, desc, leave=True, position=0):
    return tqdm(
        total=total,
        desc=desc,
        unit="item",
        ncols=100,
        ascii=True,
        leave=leave,
        position=position
    )