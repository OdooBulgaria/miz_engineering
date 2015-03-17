openerp.miz_engineering = function(instance) { 
	var _t = instance.web._t,
    _lt = instance.web._lt;
	var QWeb = instance.web.qweb;

/* Add a new mapping to the registry for image fields */
//instance.web.list.columns.add('field.image','instance.web.list.FieldBinaryImage');

/* Define a method similar to the one for forms to render image fields */
	instance.web.list.Binary= instance.web.list.Column.extend({
/**
 * Return a image to the binary field of specified as widget image
 *
 * @private
 */
	    _format: function (row_data, options) {
	        var placeholder = "/web/static/src/img/placeholder.png";
	        img_url = placeholder;
	        var text = _t("Download");
	        var value = row_data[this.id].value;
	        var download_url;
	        if (value && value.substr(0, 10).indexOf(' ') == -1) {
	            download_url = "data:application/octet-stream;base64," + value;
	        } else {
	            download_url = instance.session.url('/web/binary/saveas', {model: options.model, field: this.id, id: options.id});
	            if (this.filename) {
	                download_url += '&filename_field=' + this.filename;
	            }
	        }
	        if (this.filename && row_data[this.filename]) {
	            text = _.str.sprintf(_t("Download \"%s\""), instance.web.format_value(
	                    row_data[this.filename].value, {type: 'char'}));
	        }
	        img_url = instance.session.url('/web/binary/image', {model: options.model, field: this.id, id: options.id});
	        return _.template('<image src="<%-src%>" width="60px" height="60px"/>'+'</br>'+'<a href="<%-href%>"><%-text%></a> (<%-size%>)', {
	            src:img_url,
	            text: text,
	            href: download_url,
	            size: instance.web.binary_to_binsize(value),
	        });
	    }
	});
}