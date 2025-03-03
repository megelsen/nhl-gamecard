import pickle

__all__ = ['save_data','load_data']

def save_data(data):
    with open("cached_data.pkl", "wb") as f:
        pickle.dump(data, f)

def load_data():
    with open("cached_data.pkl", "rb") as f:
        data = pickle.load(f)
    return(data)
    