# controllers/controllers.py

from odoo import http
from odoo.http import request, Response
import json

class CineMovieController(http.Controller):

    @http.route('/api/cine/movies', auth='none', methods=['GET'], type='http')
    def get_movies(self):
        movies = request.env['cine.movie'].sudo().search_read([], ['id', 'name', 'description', 'release_date', 'image'])
        return Response(json.dumps(movies), content_type='application/json')

    @http.route('/api/cine/movie/<int:id>', auth='none', methods=['GET'], type='http')
    def get_movie(self, id):
        movie = request.env['cine.movie'].sudo().search_read([('id', '=', id)], ['id', 'name', 'description', 'release_date', 'image'])
        return Response(json.dumps(movie[0]), content_type='application/json')

    @http.route('/api/cine/movie', auth='none', methods=['POST'], type='http')
    def create_movie(self, **post):
        movie = request.env['cine.movie'].sudo().create(post)
        return Response(json.dumps(movie.id), content_type='application/json')

    @http.route('/api/cine/movie/<int:id>', auth='none', methods=['PUT'], type='http')
    def update_movie(self, id, **post):
        movie = request.env['cine.movie'].sudo().browse(id)
        movie.write(post)
        return Response(json.dumps(True), content_type='application/json')

    @http.route('/api/cine/movie/<int:id>', auth='none', methods=['DELETE'], type='http')
    def delete_movie(self, id):
        movie = request.env['cine.movie'].sudo().browse(id)
        movie.unlink()
        return Response(json.dumps(True), content_type='application/json')
