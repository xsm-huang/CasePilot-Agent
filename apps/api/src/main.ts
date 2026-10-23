import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module.js';

const app = await NestFactory.create(AppModule);
app.enableCors({ origin: 'http://localhost:5173' });
await app.listen(process.env.PORT ?? 3000);
console.log('CasePilot API running at http://localhost:3000/api');
