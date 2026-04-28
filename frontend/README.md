# OmniAegis SentinelAgent Dashboard

A brand protection and IP monitoring platform MVP built with Next.js 14, TypeScript, Tailwind CSS, and Prisma.

## Features

- **Executive Command Center**: Overview metrics and threat queue management
- **HITL Operational Queue**: Human-in-the-loop review interface for reviewers
- **RL Optimizer**: Policy comparison and training monitoring for admins
- **System Governance & Audit**: Blockchain audit ledger and privacy budget tracking for admins

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up the database:
   ```bash
   npm run prisma-generate
   npm run migrate
   npm run seed
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Authentication

Demo credentials:
- **Admin**: admin@sentinelai.com / admin123
- **Reviewer**: reviewer@sentinelai.com / reviewer123

## Project Structure

- `app/`: Next.js app router pages and API routes
- `components/`: Reusable React components
- `lib/`: Utility functions and configurations
- `prisma/`: Database schema and seed data

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: SQLite with Prisma ORM
- **Authentication**: Mock authentication with localStorage