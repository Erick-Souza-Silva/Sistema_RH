

from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
	Boolean,
	Date,
	DateTime,
	Enum as SqlEnum,
	ForeignKey,
	Numeric,
	String,
	Text,
	UniqueConstraint,
	create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


def _database_url() -> str:
	url = os.getenv("DATABASE_URL")
	if not url:
		raise RuntimeError("Defina a variável de ambiente DATABASE_URL do Neon.")
	if url.startswith("postgres://"):
		url = "postgresql+psycopg://" + url[len("postgres://") :]
	elif url.startswith("postgresql://"):
		url = "postgresql+psycopg://" + url[len("postgresql://") :]
	if "sslmode=" not in url:
		url += "&sslmode=require" if "?" in url else "?sslmode=require"
	return url


engine = create_engine(_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
	pass


class EmploymentStatus(str, Enum):
	ACTIVE = "ativo"
	INACTIVE = "inativo"
	ON_LEAVE = "afastado"


class LeaveStatus(str, Enum):
	PENDING = "pendente"
	APPROVED = "aprovado"
	REJECTED = "rejeitado"


class Department(Base):
	__tablename__ = "departamentos"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
	description: Mapped[str | None] = mapped_column(Text)
	employees: Mapped[list[Employee]] = relationship(back_populates="department")


class JobPosition(Base):
	__tablename__ = "cargos"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
	description: Mapped[str | None] = mapped_column(Text)
	employees: Mapped[list[Employee]] = relationship(back_populates="position")


class Employee(Base):
	__tablename__ = "funcionarios"
	__table_args__ = (UniqueConstraint("cpf", name="uq_funcionarios_cpf"),)

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(160), nullable=False)
	email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
	cpf: Mapped[str] = mapped_column(String(14), nullable=False)
	phone: Mapped[str | None] = mapped_column(String(25))
	hire_date: Mapped[date] = mapped_column(Date, nullable=False)
	birth_date: Mapped[date | None] = mapped_column(Date)
	salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
	status: Mapped[EmploymentStatus] = mapped_column(
		SqlEnum(EmploymentStatus), default=EmploymentStatus.ACTIVE, nullable=False
	)
	department_id: Mapped[int] = mapped_column(ForeignKey("departamentos.id"), nullable=False)
	position_id: Mapped[int] = mapped_column(ForeignKey("cargos.id"), nullable=False)
	department: Mapped[Department] = relationship(back_populates="employees")
	position: Mapped[JobPosition] = relationship(back_populates="employees")
	time_entries: Mapped[list[TimeEntry]] = relationship(back_populates="employee", cascade="all, delete-orphan")
	leaves: Mapped[list[Leave]] = relationship(back_populates="employee", cascade="all, delete-orphan")
	payrolls: Mapped[list[Payroll]] = relationship(back_populates="employee", cascade="all, delete-orphan")


class TimeEntry(Base):
	__tablename__ = "pontos"
	__table_args__ = (UniqueConstraint("employee_id", "work_date", name="uq_pontos_funcionario_data"),)

	id: Mapped[int] = mapped_column(primary_key=True)
	employee_id: Mapped[int] = mapped_column(ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
	work_date: Mapped[date] = mapped_column(Date, nullable=False)
	check_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	check_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	notes: Mapped[str | None] = mapped_column(Text)
	employee: Mapped[Employee] = relationship(back_populates="time_entries")


class Leave(Base):
	__tablename__ = "afastamentos"

	id: Mapped[int] = mapped_column(primary_key=True)
	employee_id: Mapped[int] = mapped_column(ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
	start_date: Mapped[date] = mapped_column(Date, nullable=False)
	end_date: Mapped[date] = mapped_column(Date, nullable=False)
	reason: Mapped[str] = mapped_column(String(255), nullable=False)
	status: Mapped[LeaveStatus] = mapped_column(
		SqlEnum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False
	)
	employee: Mapped[Employee] = relationship(back_populates="leaves")


class Payroll(Base):
	__tablename__ = "folhas_pagamento"
	__table_args__ = (UniqueConstraint("employee_id", "reference_month", name="uq_folha_funcionario_mes"),)

	id: Mapped[int] = mapped_column(primary_key=True)
	employee_id: Mapped[int] = mapped_column(ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
	reference_month: Mapped[date] = mapped_column(Date, nullable=False)
	gross_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
	deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
	net_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
	paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	employee: Mapped[Employee] = relationship(back_populates="payrolls")


def create_tables() -> None:
	"""Cria as tabelas no Neon (use migrações em produção)."""
	Base.metadata.create_all(engine)
