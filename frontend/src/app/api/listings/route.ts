
import { NextResponse } from 'next/server';
import { PrismaClient } from '@/generated/prisma';

const prisma = new PrismaClient();

export async function GET() {
  try {
    const listings = await prisma.listing.findMany({
      include: {
        user: true,
        category: true,
        images: true,
      },
      where: {
        status: 'active',
      },
    });
    return NextResponse.json(listings);
  } catch (error) {
    console.error('Error fetching listings:', error);
    return NextResponse.json({ error: 'Failed to fetch listings' }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}
