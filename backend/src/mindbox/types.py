from enum import StrEnum


class CourseProgressStatus(StrEnum):
    """Course progress status in Mindbox"""

    PROGRESS_1 = "1PercentProgress"
    PROGRESS_5 = "5PercentProgress"
    PROGRESS_10 = "10PercentProgress"
    PROGRESS_25 = "25PercentProgress"
    PROGRESS_50 = "50PercentProgress"
    PROGRESS_75 = "75PercentProgress"
    PROGRESS_90 = "90PercentProgress"
    FINISHED = "CourseFinished"
