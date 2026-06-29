import { NextRequest, NextResponse } from 'next/server';

const PASSWORD = 'adonis2026';
const COOKIE_NAME = 'adonis_auth';

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Allow login page and its API route through
  if (pathname === '/login' || pathname === '/api/login') {
    return NextResponse.next();
  }

  const cookie = req.cookies.get(COOKIE_NAME);
  if (cookie?.value === PASSWORD) {
    return NextResponse.next();
  }

  const loginUrl = req.nextUrl.clone();
  loginUrl.pathname = '/login';
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
