-- CreateEnum
CREATE TYPE "FixedIncomeType" AS ENUM ('CDB', 'TREASURY_DIRECT', 'LCI_LCA');

-- CreateTable
CREATE TABLE "FixedIncomePosition" (
    "id" TEXT NOT NULL,
    "institution" TEXT NOT NULL,
    "type" "FixedIncomeType" NOT NULL,
    "description" TEXT,
    "appliedAt" TIMESTAMP(3) NOT NULL,
    "appliedAmountCents" BIGINT NOT NULL,
    "contractedRate" TEXT,
    "maturityDate" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "FixedIncomePosition_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "FixedIncomeValueUpdate" (
    "id" TEXT NOT NULL,
    "positionId" TEXT NOT NULL,
    "amountCents" BIGINT NOT NULL,
    "asOf" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "FixedIncomeValueUpdate_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "FixedIncomeValueUpdate" ADD CONSTRAINT "FixedIncomeValueUpdate_positionId_fkey" FOREIGN KEY ("positionId") REFERENCES "FixedIncomePosition"("id") ON DELETE CASCADE ON UPDATE CASCADE;
