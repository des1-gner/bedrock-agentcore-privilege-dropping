# Test written by Oisin@AWS
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from strands import Agent
import os
import pwd
import grp

app = FastAPI(title="Strands Agent Server", version="1.0.0")

def drop_privileges():
    """Drop root privileges and switch to a non-root user"""
    try:
        # Get the test user info
        test_user = pwd.getpwnam('test')
        test_group = grp.getgrnam('test')
        
        # Switch to test user
        os.setgid(test_group.gr_gid)
        os.setuid(test_user.pw_uid)
        
        # Verify the switch worked
        return {
            "switched": True,
            "new_uid": os.getuid(),
            "new_gid": os.getgid(),
            "new_username": pwd.getpwuid(os.getuid()).pw_name
        }
    except Exception as e:
        return {"switched": False, "error": str(e)}

# ADD THIS: FastAPI startup event to drop privileges when the app starts
@app.on_event("startup")
async def startup_event():
    print(f"Starting up - Current UID: {os.getuid()}")
    if os.getuid() == 0:  # If running as root
        print("Running as root, attempting to drop privileges...")
        result = drop_privileges()
        print(f"Privilege drop result: {result}")
    else:
        print("Not running as root, no privilege drop needed")

# Initialise Strands agent AFTER the startup event is defined
strands_agent = Agent()

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    try:
        user_message = request.input.get("prompt", "")
        if not user_message:
            raise HTTPException(
                status_code=400, 
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )

        result = strands_agent(user_message)
        
        # Get system info (this will now show the dropped privileges)
        system_data = {}
        try:
            uid = os.getuid()
            gid = os.getgid()
            
            try:
                user_info = pwd.getpwuid(uid)
                username = user_info.pw_name
            except:
                username = f"uid_{uid}"
                
            try:
                group_info = grp.getgrgid(gid)
                groupname = group_info.gr_name
            except:
                groupname = f"gid_{gid}"
                
            system_data = {
                "user_id": uid,
                "group_id": gid,
                "username": username,
                "groupname": groupname,
                "working_directory": os.getcwd(),
                "env_USER": os.environ.get('USER', 'not_set'),
                "process_id": os.getpid()
            }
        except Exception as e:
            system_data = {"error": str(e)}
        
        response = {
            "message": result.message,
            "timestamp": datetime.utcnow().isoformat(),
            "model": "strands-agent",
            "system_info": system_data
        }

        return InvocationResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.get("/ping")
async def ping():
    try:
        # Get system info for ping as well
        uid = os.getuid()
        gid = os.getgid()
        
        try:
            user_info = pwd.getpwuid(uid)
            username = user_info.pw_name
        except:
            username = f"uid_{uid}"
            
        try:
            group_info = grp.getgrgid(gid)
            groupname = group_info.gr_name
        except:
            groupname = f"gid_{gid}"
        
        return {
            "status": "healthy",
            "system_info": {
                "user_id": uid,
                "group_id": gid,
                "username": username,
                "groupname": groupname,
                "working_directory": os.getcwd(),
                "env_USER": os.environ.get('USER', 'not_set'),
                "process_id": os.getpid()
            }
        }
    except Exception as e:
        return {"status": "healthy", "system_error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)