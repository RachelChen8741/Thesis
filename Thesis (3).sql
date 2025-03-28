CREATE TABLE "allergies" (
  "start" date,
  "stop" date,
  "patient" uuid,
  "encounter" uuid,
  "code" bigserial,
  "system" text,
  "description" text,
  "type" text,
  "category" text,
  "reaction1" text,
  "description1" text,
  "severity1" text,
  "reaction2" text,
  "description2" text,
  "severity2" text
);

CREATE TABLE "careplans" (
  "id" uuid PRIMARY KEY,
  "start" date,
  "stop" date,
  "patient" uuid,
  "encounter" uuid,
  "code" text,
  "description" text,
  "reasoncode" text,
  "reasondescription" text
);

CREATE TABLE "claims" (
  "id" uuid PRIMARY KEY,
  "patient" uuid,
  "provider" uuid,
  "primaryinsurance" uuid,
  "secondaryinsurance" uuid,
  "departmentid" integer,
  "patientdepid" integer,
  "diagnosis1" bigserial,
  "diagonsis2" bigserial,
  "diagnosis3" bigserial,
  "diagonsis4" bigserial,
  "diagnosis5" bigserial,
  "diagonsis6" bigserial,
  "diagnosis7" bigserial,
  "diagnosis8" bigserial,
  "referid" uuid,
  "appointmentid" uuid,
  "currbilldate" date,
  "servicedate" date,
  "supprovideid" uuid,
  "status1" text,
  "status2" text,
  "statusp" text,
  "outstanding1" numeric,
  "outstanding2" numeric,
  "outstandingp" numeric,
  "lastbilldate1" date,
  "lastbilldate2" date,
  "lastbilldatep" date,
  "healthcareid1" numeric,
  "healthcareid2" numeric
);

CREATE TABLE "claims_transactions" (
  "id" uuid PRIMARY KEY,
  "claimid" uuid,
  "chargeid" numeric,
  "patient" uuid,
  "type" text,
  "amount" numeric,
  "method" text,
  "fromdate" date,
  "todate" date,
  "place" uuid,
  "procedurecode" text,
  "modifier1" text,
  "modifier2" text,
  "diagonsisref1" integer,
  "diagnosisref2" integer,
  "diagonsisref3" integer,
  "diagnosisref4" integer,
  "units" numeric,
  "deparatmentid" integer,
  "notes" text,
  "unitamount" numeric,
  "transferoutid" integer,
  "transfertype" text,
  "payments" numeric,
  "adjustments" numeric,
  "transfers" numeric,
  "outstanding" numeric,
  "appointmentid" uuid,
  "linenote" text,
  "patientinsurid" uuid,
  "feeschedid" integer,
  "providerid" uuid,
  "supervisingproviderid" uuid
);

CREATE TABLE "conditions" (
  "start" date,
  "stop" date,
  "patient" uuid,
  "encounter" uuid,
  "system" text,
  "code" text,
  "description" text
);

CREATE TABLE "devices" (
  "start" date,
  "stop" date,
  "patient" uuid,
  "encounter" uuid,
  "code" text,
  "description" text,
  "UDI" text
);

CREATE TABLE "encounters" (
  "id" uuid PRIMARY KEY,
  "start" date,
  "stop" date,
  "patient" uuid,
  "organization" uuid,
  "provider" uuid,
  "payer" uuid,
  "encounterclass" text,
  "code" text,
  "description" text,
  "base_encounter_cost" numeric,
  "total_claim_cost" numeric,
  "payer_coverage" numeric,
  "reasoncode" text,
  "reasondescription" text
);

CREATE TABLE "imaging" (
  "id" uuid,
  "date" date,
  "patient" uuid,
  "encounter" uuid,
  "seriesuid" text,
  "bodysitecode" text,
  "bodysitedescription" text,
  "modalitycode" text,
  "modalitydescription" text,
  "instanceuid" text,
  "sopcode" text,
  "sopdescription" text,
  "procedurecode" text
);

CREATE TABLE "immunizations" (
  "date" date,
  "patient" uuid,
  "encounter" uuid,
  "code" bigserial,
  "description" text,
  "cost" numeric
);

CREATE TABLE "medications" (
  "start" date,
  "stop" date,
  "patient" uuid,
  "payer" uuid,
  "encounter" uuid,
  "code" text,
  "description" text,
  "base_cost" numeric,
  "payer_coverage" numeric,
  "dispenses" numeric,
  "totalcost" numeric,
  "reasoncode" text,
  "reasondescription" text
);

CREATE TABLE "observations" (
  "date" date,
  "patient" uuid,
  "encounter" uuid,
  "category" text,
  "code" text,
  "description" text,
  "value" text,
  "units" text,
  "type" text
);

CREATE TABLE "organizations" (
  "id" uuid PRIMARY KEY,
  "name" text,
  "address" text,
  "city" text,
  "state" text,
  "zip" text,
  "lat" numeric,
  "lon" numeric,
  "phone" text,
  "revenue" numeric,
  "utilization" numeric
);

CREATE TABLE "patients" (
  "id" uuid PRIMARY KEY,
  "birthdate" date,
  "deathdate" date,
  "ssn" text,
  "drivers" text,
  "passport" text,
  "prefix" text,
  "first" text,
  "middle" text,
  "last" text,
  "suffix" text,
  "maiden" text,
  "martial" text,
  "race" text,
  "ethnicity" text,
  "gender" text,
  "birthplace" text,
  "address" text,
  "city" text,
  "state" text,
  "county" text,
  "FIPScountrycode" text,
  "zip" text,
  "lat" numeric,
  "lon" numeric,
  "healthcare_expense" numeric,
  "healthcare_coverage" numeric,
  "income" numeric
);

CREATE TABLE "payertransitions" (
  "patient" uuid,
  "memberid" uuid,
  "startyear" date,
  "endyear" date,
  "payer" uuid,
  "secondarypayer" uuid,
  "ownership" text,
  "ownername" text
);

CREATE TABLE "payers" (
  "id" uuid PRIMARY KEY,
  "name" text,
  "ownership" text,
  "address" text,
  "city" text,
  "states_headquartered" text,
  "zip" text,
  "phone" text,
  "amount_covered" numeric,
  "amount_uncovered" numeric,
  "revenue" numeric,
  "covered_encounters" numeric,
  "uncovered_encounters" numeric,
  "covered_medications" numeric,
  "uncovered_medications" numeric,
  "covered_procedures" numeric,
  "uncovered_procedures" numeric,
  "covered_immunizations" numeric,
  "unconvered_immunizations" numeric,
  "unique_customers" numeric,
  "QOLS_avg" numeric,
  "member_months" numeric
);

CREATE TABLE "procedures" (
  "start" date,
  "stop" date,
  "patient" uuid,
  "encounter" uuid,
  "system" text,
  "code" text,
  "description" text,
  "base_cost" numeric,
  "reasoncode" text,
  "reasondescription" text
);

CREATE TABLE "providers" (
  "id" uuid PRIMARY KEY,
  "organization" uuid,
  "name" text,
  "gender" text,
  "speciality" text,
  "address" text,
  "city" text,
  "state" text,
  "zip" text,
  "lat" numeric,
  "lon" numeric,
  "encounters" numeric,
  "procedures" numeric
);

CREATE TABLE "supplies" (
  "date" date,
  "patient" uuid,
  "encounter" uuid,
  "code" text,
  "description" text,
  "quantity" numeric
);

ALTER TABLE "allergies" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "allergies" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "careplans" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "careplans" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "claims" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "claims" ADD FOREIGN KEY ("provider") REFERENCES "providers" ("id");

ALTER TABLE "claims" ADD FOREIGN KEY ("primaryinsurance") REFERENCES "payers" ("id");

ALTER TABLE "claims" ADD FOREIGN KEY ("secondaryinsurance") REFERENCES "payers" ("id");

ALTER TABLE "claims" ADD FOREIGN KEY ("referid") REFERENCES "providers" ("id");

ALTER TABLE "claims" ADD FOREIGN KEY ("appointmentid") REFERENCES "encounters" ("id");

ALTER TABLE "claims" ADD FOREIGN KEY ("supprovideid") REFERENCES "providers" ("id");

ALTER TABLE "claims_transactions" ADD FOREIGN KEY ("claimid") REFERENCES "claims" ("id");

ALTER TABLE "claims_transactions" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "claims_transactions" ADD FOREIGN KEY ("place") REFERENCES "organizations" ("id");

ALTER TABLE "claims_transactions" ADD FOREIGN KEY ("appointmentid") REFERENCES "encounters" ("id");

-- ALTER TABLE "claims_transactions" ADD FOREIGN KEY ("patientinsurid") REFERENCES "payertransitions" ("memberid");

ALTER TABLE "claims_transactions" ADD FOREIGN KEY ("providerid") REFERENCES "providers" ("id");

ALTER TABLE "claims_transactions" ADD FOREIGN KEY ("supervisingproviderid") REFERENCES "providers" ("id");

ALTER TABLE "conditions" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "conditions" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "devices" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "devices" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "encounters" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "encounters" ADD FOREIGN KEY ("organization") REFERENCES "organizations" ("id");

ALTER TABLE "encounters" ADD FOREIGN KEY ("provider") REFERENCES "providers" ("id");

ALTER TABLE "encounters" ADD FOREIGN KEY ("payer") REFERENCES "payers" ("id");

ALTER TABLE "imaging" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "imaging" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "immunizations" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "immunizations" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "medications" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "medications" ADD FOREIGN KEY ("payer") REFERENCES "payers" ("id");

ALTER TABLE "medications" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "observations" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "observations" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "payertransitions" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "payertransitions" ADD FOREIGN KEY ("payer") REFERENCES "payers" ("id");

ALTER TABLE "payertransitions" ADD FOREIGN KEY ("secondarypayer") REFERENCES "payers" ("id");

ALTER TABLE "procedures" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "procedures" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

ALTER TABLE "providers" ADD FOREIGN KEY ("organization") REFERENCES "organizations" ("id");

ALTER TABLE "supplies" ADD FOREIGN KEY ("patient") REFERENCES "patients" ("id");

ALTER TABLE "supplies" ADD FOREIGN KEY ("encounter") REFERENCES "encounters" ("id");

