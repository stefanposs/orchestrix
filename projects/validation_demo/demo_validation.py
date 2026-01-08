from dataclasses import dataclass
from orchestrix import Command

@dataclass(frozen=True, kw_only=True)
class RegisterUser(Command):
    user_id: str
    email: str
    password: str
    
    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError("Invalid email")
        if len(self.password) < 8:
            raise ValueError("Password too short")

# Usage: try creating RegisterUser with invalid data to see validation
