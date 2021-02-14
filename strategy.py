import shutil

# =========================================
NODOWN = -1
PADDING = 0
DOWNLOAD = 1
# =========================================

"""
def FIFO(source):
    global freeSize
    while(len(state)):
        if(freeSize > source.size):
            break 
        oldSource = state.pop(0)
        path = os.path.join(downloadPath, oldSource.savepath)
        shutil.rmtree(path) 
        freeSize += oldSource.size 

    state.append(source)

def checkSize():
    pass
"""

def downloadFree(seed, context):
    print(seed.name)
    print(seed.seedType)
    if seed.seedType == 'free_bg':
        return DOWNLOAD
    return PADDING

strategyPriorityQueue = []
strategyPriorityQueue.append(downloadFree)