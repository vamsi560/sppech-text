from typing import Optional

from pydantic import BaseModel, Field


class ExtractedInfo(BaseModel):
    name: Optional[str] = Field(default=None)
    mobile_number: Optional[str] = Field(default=None)
    submission_number: Optional[str] = Field(default=None)

    def normalized_mobile(self) -> Optional[str]:
        if not self.mobile_number:
            return None
        digits = "".join(ch for ch in self.mobile_number if ch.isdigit())
        return digits or None


