from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from itertools import groupby
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
    id: UUID
    name: str
    time_slot: TimeSlot


@dataclass(frozen=True)
class ContactInfo(object):
    parent_phone_number: str
    student_phone_number: str = ""


class AttendanceStatus(Enum):
    ABSENT = 0
    LATE = 1
    PRESENT = 2


@dataclass(frozen=True)
class Attendance(object):
    date: date
    class_: Class
    status: AttendanceStatus


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
    attendances: List[Attendance] = field(default_factory=list)


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


def show_class_name(cls: Class) -> str:
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


@dataclass(frozen=True)
class AttendanceRecord(object):
    class_name: str
    days_absent: int
    days_late: int
    days_present: int
    total_days: int
    percentage: int


class StudentListView(TypedDict):
    students: List[ListableStudent]


class StudentDetailView(TypedDict):
    student_profile: StudentProfile
    student_detail: StudentDetail


class StudentAttendanceView(TypedDict):
    student_profile: StudentProfile
    attendance_records: List[AttendanceRecord]


def create_listable_student(student: Student) -> ListableStudent:
    return ListableStudent(
        id=str(student.id),
        name=student.name,
        status=show_status(student.status),
        classes=[show_class_name(c) for c in sorted(student.classes, key=lambda c: c.time_slot)])


def create_student_list_view(students_: List[Student]) -> StudentListView:
    return dict(students=[create_listable_student(s) for s in students_])


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
        classes=[show_class_name(c) for c in sorted(student.classes, key=lambda c: c.time_slot)])


def create_student_detail_view(student: Student) -> StudentDetailView:
    return dict(
        student_profile=create_student_profile(student),
        student_detail=create_student_detail(student))


def create_class_attendance(cls: Class, attendances: List[Attendance]) -> AttendanceRecord:
    def attendances_for(status: AttendanceStatus) -> int:
        return len([a for a in attendances if a.status is status])

    def days_late() -> int:
        return attendances_for(AttendanceStatus.LATE)

    def days_present() -> int:
        return attendances_for(AttendanceStatus.PRESENT)

    def days_absent() -> int:
        return attendances_for(AttendanceStatus.ABSENT)

    def total_days() -> int:
        return len(list(attendances))

    def percentage() -> int:
        return round(
            (100 / total_days())
            * (days_present() + days_late()))

    return AttendanceRecord(
        class_name=show_class_name(cls),
        days_absent=days_absent(),
        days_present=days_present(),
        days_late=days_late(),
        total_days=total_days(),
        percentage=percentage())


def create_attendance_records(student: Student) -> List[AttendanceRecord]:
    sorted_attendances = sorted(student.attendances, key=lambda a: a.class_.id)
    grouped_attendances = groupby(sorted_attendances, key=lambda a: a.class_)
    return [create_class_attendance(cls, list(attendances))
            for (cls, attendances) in grouped_attendances]


def create_student_attendance_view(student: Student) -> StudentAttendanceView:
    return dict(
        student_profile=create_student_profile(student),
        attendance_records=create_attendance_records(student),
        today=date.today()
    )


class1 = Class(
    id=UUID('aa36e8cf-4cde-4054-b813-511dbca4e08c'),
    name="국체반 Claire",
    time_slot=TimeSlot(6, 20, Period.PM))

class2 = Class(
    id=UUID('aade1d34-20d1-4dd5-a302-9b953bb33181'),
    name="우선미 선생님",
    time_slot=TimeSlot(8, 10, Period.PM))

class3 = Class(
    id=UUID('9b944a27-889f-45f1-863d-7f1ce4c96f04'),
    name="우선미 선생님",
    time_slot=TimeSlot(8, 10, Period.PM))

students = [
    Student(
        id=UUID("8f3f55cf-de69-4e70-82d4-aac0ca82d9ee"),
        name="이채원",
        date_of_birth=date(2005, 1, 22),
        gender=Gender.FEMALE,
        contact=ContactInfo("010-2345-6789"),
        date_joined=date(2018, 5, 13),
        status=Status.NONE,
        classes=[class1],
        attendances=[
            Attendance(date(2020, 6, 1), class1, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 29), class1, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 28), class1, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 27), class1, AttendanceStatus.ABSENT),
            Attendance(date(2020, 5, 26), class1, AttendanceStatus.LATE),
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
        classes=[class1, class2],
        attendances=[
            Attendance(date(2020, 6, 1), class1, AttendanceStatus.PRESENT),
            Attendance(date(2020, 6, 1), class2, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 29), class1, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 29), class2, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 28), class1, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 28), class2, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 27), class1, AttendanceStatus.ABSENT),
            Attendance(date(2020, 5, 27), class2, AttendanceStatus.LATE),
            Attendance(date(2020, 5, 29), class1, AttendanceStatus.PRESENT),
            Attendance(date(2020, 5, 26), class1, AttendanceStatus.LATE),
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
        classes=[class3],
        attendances=[
            Attendance(date(2020, 6, 1), class3, AttendanceStatus.ABSENT),
            Attendance(date(2020, 5, 29), class3, AttendanceStatus.ABSENT),
            Attendance(date(2020, 5, 28), class3, AttendanceStatus.ABSENT),
            Attendance(date(2020, 5, 27), class3, AttendanceStatus.ABSENT),
            Attendance(date(2020, 5, 26), class3, AttendanceStatus.ABSENT),
        ],
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
