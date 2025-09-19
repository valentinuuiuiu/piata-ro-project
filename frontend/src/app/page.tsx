'use client';

import { useState, useEffect } from 'react';

import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Search } from 'lucide-react'


interface Listing {
  id: number;
  title: string;
  description: string;
  price?: number;
  currency: string;
  location: string;
  user: {
    username: string;
  };
  category: {
    name: string;
  };
  images: {
    image: string;
    is_main: boolean;
  }[];
}

export default function Home() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/listings')
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          setListings(data);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError('Failed to fetch listings');
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  if (error) return <div className="flex justify-center items-center min-h-screen text-red-500">Error: {error}</div>;

  return (
    <main className="container mx-auto p-4 min-h-screen">
      <div className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight text-center">Piata RO - Marketplace</h1>
        <p className="text-muted-foreground text-center mt-2">Discover amazing deals in Romania</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {listings.map((listing) => (
          <Card key={listing.id} className="overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="p-0">
              {listing.images.length > 0 && (
                <img
                  src={listing.images.find((img) => img.is_main)?.image || '/placeholder.jpg'}
                  alt={listing.title}
                  className="w-full h-48 object-cover"
                />
              )}
            </CardHeader>
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-2">
                <h2 className="text-xl font-semibold">{listing.title}</h2>
                <Badge variant="secondary" className="ml-2">{listing.category.name}</Badge>
              </div>
              <p className="text-muted-foreground mb-4 line-clamp-3">{listing.description}</p>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={`https://avatar.letters.to/${listing.user.username}`} />
                    <AvatarFallback>{listing.user.username[0]}</AvatarFallback>
                  </Avatar>
                  <span className="text-sm font-medium">{listing.user.username}</span>
                </div>
                <p className="text-sm text-muted-foreground">📍 {listing.location}</p>
              </div>
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-green-600">
                  {listing.price ? `${listing.price} ${listing.currency}` : 'Free'}
                </h3>
                <Button variant="outline" size="sm">View Details</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {listings.length === 0 && (
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
          <Search className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No listings available yet</h3>
          <p className="text-muted-foreground">Check back soon for amazing deals!</p>
        </div>
      )}
    </main>
  );
}

