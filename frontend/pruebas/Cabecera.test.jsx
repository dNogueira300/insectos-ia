import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Cabecera from '../src/compartido/Cabecera.jsx'
import Pie from '../src/compartido/Pie.jsx'

describe('Cabecera', () => {
  it('enlaza al inicio, al catálogo, a los créditos y a la herramienta', () => {
    render(<Cabecera pagina="inicio" />)
    expect(screen.getByRole('link', { name: /INSECTIA, inicio/ })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Catálogo' })).toHaveAttribute('href', '/catalogo/')
    expect(screen.getByRole('link', { name: 'Créditos' })).toHaveAttribute('href', '/creditos/')
    expect(screen.getByRole('link', { name: 'Identificar un insecto' })).toHaveAttribute('href', '/identificar/')
  })

  it('marca la página actual', () => {
    render(<Cabecera pagina="identificar" />)
    expect(screen.getByRole('link', { name: 'Identificar un insecto' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: 'Inicio' })).not.toHaveAttribute('aria-current')
  })

  it('marca el catálogo y los créditos cuando son la página actual', () => {
    const { unmount } = render(<Cabecera pagina="catalogo" />)
    expect(screen.getByRole('link', { name: 'Catálogo' })).toHaveAttribute('aria-current', 'page')
    unmount()
    render(<Cabecera pagina="creditos" />)
    expect(screen.getByRole('link', { name: 'Créditos' })).toHaveAttribute('aria-current', 'page')
  })

  it('el menú del celular se abre y se cierra con su botón', () => {
    render(<Cabecera pagina="inicio" />)
    const boton = screen.getByRole('button', { name: 'Abrir el menú' })
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    expect(boton).toHaveAttribute('aria-controls', 'menu-principal')
    expect(document.getElementById('menu-principal')).toBe(screen.getByRole('navigation', { name: 'Principal' }))

    fireEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    expect(boton).toHaveAccessibleName('Cerrar el menú')
    expect(document.querySelector('.cabecera')).toHaveClass('cabecera--abierta')

    fireEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    expect(document.querySelector('.cabecera')).not.toHaveClass('cabecera--abierta')
  })

  it('el menú se cierra con Escape, devuelve el foco, y al tocar fuera', () => {
    render(<Cabecera pagina="inicio" />)
    const boton = screen.getByRole('button', { name: 'Abrir el menú' })

    fireEvent.click(boton)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    expect(boton).toHaveFocus()

    fireEvent.click(boton)
    fireEvent.pointerDown(screen.getByRole('link', { name: 'Catálogo' }))
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    fireEvent.pointerDown(document.body)
    expect(boton).toHaveAttribute('aria-expanded', 'false')
  })
})

describe('Pie', () => {
  it('da el crédito de las fotos y no nombra personas', () => {
    render(<Pie corrida="v4_convnext_t_288" />)
    expect(screen.getByText(/Fotos: iNaturalist/)).toBeInTheDocument()
    expect(screen.getByText(/v4_convnext_t_288/)).toBeInTheDocument()
    expect(screen.queryByText(/Dra\.|Dr\./)).not.toBeInTheDocument()
  })

  it('enlaza al catálogo y a los créditos', () => {
    render(<Pie />)
    expect(screen.getByRole('link', { name: 'Catálogo' })).toHaveAttribute('href', '/catalogo/')
    expect(screen.getByRole('link', { name: 'Créditos' })).toHaveAttribute('href', '/creditos/')
  })
})
