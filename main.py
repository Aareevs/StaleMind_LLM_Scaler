from fastapi import FastAPI
from pydantic import BaseModel
from env.environment import StaleMindEnv as DriftGym

app = FastAPI()

env = DriftGym()
env.reset()


@app.get("/")
def home():
    return {"message": "StaleMind API running"}


class Action(BaseModel):
    type: str
    content: str = ""

@app.post("/reset")
def reset():
    obs = env.reset()
    return {"observation": obs}


@app.post("/step")
def step(action: Action):
    obs, reward, done, _ = env.step(action.model_dump() if hasattr(action, 'model_dump') else action.dict())
    return {
        "observation": obs,
        "reward": {"score": reward},
        "done": done
    }


@app.get("/state")
def state():
    return env.state()
