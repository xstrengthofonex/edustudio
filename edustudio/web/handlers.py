from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, NamedTuple, Optional, TypedDict
from uuid import UUID

import aiohttp_jinja2
from aiohttp import web
from dateutil.relativedelta import relativedelta

from edustudio.web.app import Handler


class Gender(Enum):
    FEMALE = 0
    MALE = 1


class Status(Enum):
    NONE = 0
    BREAK = 1


class Period(Enum):
    AM = 0
    PM = 1


class TimeSlot(NamedTuple):
    hours: int
    minutes: int
    period: Period


@dataclass(frozen=True)
class Class(object):
    name: str
    time_slot: TimeSlot


@dataclass(frozen=True)
class ContactInfo(object):
    parent_phone_number: str


@dataclass(frozen=True)
class Student(object):
    id: UUID
    name: str
    date_of_birth: date
    gender: Gender
    date_joined: date
    status: Status
    contact: ContactInfo
    classes: List[Class] = field(default_factory=list)


@dataclass(frozen=True)
class ListableStudent(object):
    id: str
    name: str
    status: str
    classes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class StudentDetail(object):
    id: str
    name: str
    age: int
    gender: str
    parent_phone_number: str
    date_joined: str
    status: str
    classes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class StudentProfile:
    id: str
    name: str
    parent_phone_number: str
    status: str


def calculate_age(today: date, date_of_birth: date) -> int:
    age = relativedelta(today, date_of_birth)
    return age.years


def show_class(cls: Class) -> str:
    def show_period(period: Period) -> str:
        return {
            Period.AM: "AM",
            Period.PM: "PM"
        }.get(period, "")
    return f"{cls.time_slot.hours}:{cls.time_slot.minutes}{show_period(cls.time_slot.period)} {cls.name}"


def show_gender(gender: Gender) -> str:
    return {
        Gender.FEMALE: "여",
        Gender.MALE: "남"
    }.get(gender, "")


def show_status(status: Status) -> str:
    return {
        Status.NONE: "",
        Status.BREAK: "휴원"
    }.get(status, "")


def show_date_joined(date_joined: date) -> str:
    return str(date_joined)


class StudentListView(TypedDict):
    students: List[ListableStudent]


class StudentDetailView(TypedDict):
    student_profile: StudentProfile
    student_detail: StudentDetail


class StudentAttendanceView(TypedDict):
    student_profile: StudentProfile


def create_student_list_view(students_: List[Student]) -> StudentListView:
    def make_listable_student(student: Student) -> ListableStudent:
        return ListableStudent(
            id=str(student.id),
            name=student.name,
            status=show_status(student.status),
            classes=[show_class(c) for c in sorted(student.classes, key=lambda c: c.time_slot)])
    return dict(students=[make_listable_student(s) for s in students_])


def create_student_profile(student: Student) -> StudentProfile:
    return StudentProfile(
        id=str(student.id),
        name=student.name,
        status=show_status(student.status),
        parent_phone_number=student.contact.parent_phone_number)


def create_student_detail(student: Student) -> StudentDetail:
    return StudentDetail(
        id=str(student.id),
        name=student.name,
        age=calculate_age(date.today(), student.date_of_birth),
        gender=show_gender(student.gender),
        parent_phone_number=student.contact.parent_phone_number,
        date_joined=show_date_joined(student.date_joined),
        status=show_status(student.status),
        classes=[show_class(c) for c in sorted(student.classes, key=lambda c: c.time_slot)])


def create_student_detail_view(student: Student) -> StudentDetailView:
    return dict(
        student_profile=create_student_profile(student),
        student_detail=create_student_detail(student))


def create_student_attendance_view(student: Student) -> StudentAttendanceView:
    return dict(
        student_profile=create_student_profile(student))


students = [
    Student(
        id=UUID("8f3f55cf-de69-4e70-82d4-aac0ca82d9ee"),
        name="이채원",
        date_of_birth=date(2005, 1, 22),
        gender=Gender.FEMALE,
        contact=ContactInfo("010-2345-6789"),
        date_joined=date(2018, 5, 13),
        status=Status.NONE,
        classes=[
            Class("국체반 Claire", TimeSlot(6, 20, Period.PM))
        ]
    ),
    Student(
        id=UUID("73af91aa-1a88-4fd9-8ffa-b31297d1dcdd"),
        name="김대현",
        date_of_birth=date(2006, 3, 1),
        gender=Gender.MALE,
        contact=ContactInfo("010-2345-6789"),
        date_joined=date(2017, 2, 2),
        status=Status.NONE,
        classes=[
            Class("국체반 Claire", TimeSlot(6, 20, Period.PM)),
            Class("우선미 선생님", TimeSlot(8, 10, Period.PM))
        ]
    ),
    Student(
        id=UUID("65cb2dc9-95b4-4cb6-987d-78a9db5e2c8b"),
        name="박은경",
        date_of_birth=date(2003, 6, 10),
        gender=Gender.FEMALE,
        contact=ContactInfo("010-2345-6789"),
        date_joined=date(2016, 10, 24),
        status=Status.BREAK,
        classes=[
            Class("진", TimeSlot(5, 10, Period.PM))
        ]
    ),
]


@aiohttp_jinja2.template("home.jinja2")
async def handle_home(_: web.Request):
    return dict()


def create_student_list_handler() -> Handler:
    @aiohttp_jinja2.template("students/list.jinja2")
    async def handle(_: web.Request) -> dict:
        return create_student_list_view(students)
    return handle


def get_student(student_id: str) -> Optional[Student]:
    return next((s for s in students if str(s.id) == student_id), None)


def create_student_detail_handler() -> Handler:
    @aiohttp_jinja2.template("students/detail.jinja2")
    async def handle(request: web.Request) -> dict:
        if student_id := request.match_info.get("student_id"):
            if student := get_student(student_id):
                return create_student_detail_view(student)
        raise web.HTTPNotFound()
    return handle


def create_student_attendance_handler():
    @aiohttp_jinja2.template("students/attendance.jinja2")
    async def handle(request: web.Request) -> dict:
        if student_id := request.match_info.get("student_id"):
            if student := get_student(student_id):
                return create_student_attendance_view(student)
        raise web.HTTPNotFound()
    return handle
