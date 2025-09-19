
const { PrismaClient } = require('../src/generated/prisma');

const prisma = new PrismaClient();

async function main() {
  // Create sample categories
  const electronics = await prisma.category.upsert({
    where: { slug: 'electronics' },
    update: {},
    create: {
      name: 'Electronics',
      slug: 'electronics',
      icon: '📱',
      color: '#4F46E5',
    },
  });

  const phones = await prisma.category.upsert({
    where: { slug: 'phones' },
    update: {},
    create: {
      name: 'Phones',
      slug: 'phones',
      icon: '📱',
      color: '#10B981',
      parentId: electronics.id,
    },
  });

  const clothing = await prisma.category.upsert({
    where: { slug: 'clothing' },
    update: {},
    create: {
      name: 'Clothing',
      slug: 'clothing',
      icon: '👕',
      color: '#EF4444',
    },
  });

  const shirts = await prisma.category.upsert({
    where: { slug: 'shirts' },
    update: {},
    create: {
      name: 'Shirts',
      slug: 'shirts',
      icon: '👕',
      color: '#F59E0B',
      parentId: clothing.id,
    },
  });

  // Create sample user
  const user = await prisma.user.upsert({
    where: { username: 'testuser' },
    update: {},
    create: {
      username: 'testuser',
      email: 'test@example.com',
      password: 'hashedpassword',
      first_name: 'Test',
      last_name: 'User',
    },
  });

  // Create sample listing
  const existingListing = await prisma.listing.findFirst({
    where: { title: 'Sample Phone' },
  });

  let listing;
  if (!existingListing) {
    listing = await prisma.listing.create({
      data: {
        title: 'Sample Phone',
        description: 'A great phone for sale.',
        price: 500.0,
        currency: 'RON',
        location: 'Bucharest',
        userId: user.id,
        categoryId: phones.id,
        status: 'active',
      },
    });
  } else {
    listing = existingListing;
  }

  // Create sample listing image if not exists
  const existingImage = await prisma.listingImage.findFirst({
    where: {
      listingId: listing.id,
      image: 'phone.jpg',
    },
  });

  if (!existingImage) {
    await prisma.listingImage.create({
      data: {
        listingId: listing.id,
        image: 'phone.jpg',
        is_main: true,
        order: 1,
      },
    });
  }

  console.log('Seeding completed');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

